# AUTO PARSER

基于 [Kaitai Struct](https://kaitai.io) 的配置化数据包解析工具。包结构定义在 `ksy/*.ksy` 中（**唯一真源**，按版本分目录），由 Kaitai 编译器生成 Python 解析器到 `generated/`，再通过 `main.py` 按配置注册的解析器对源文件进行切片解析，输出 CSV / JSON。

## 目录结构

```
auto_parser/
├── main.py                    # 入口：选择解析器 -> 切片解析 -> 输出
├── requirement.txt            # 依赖清单（含测试用 pytest）
├── README.md                  # 本文档
├── CHANGELOG.md               # 版本日志
├── .gitignore
├── .vscode/                   # 任务（编译 / 运行 / 测试）与解释器配置
├── conf/
│   └── conf.json              # PARSER 注册表 + OUTPUT_TYPE + CRC_ALGO 算法表
├── ksy/                       # ★ 唯一真源：Kaitai 定义 (.ksy)，按版本分组
│   ├── grid1x/                # GRID-1X：hk(187B)、hk_178(178B)、ft(grid/yingtian 两版)、wf、es
│   ├── grid11b/               # GRID-11B：遥测（96B，HEAD/TAIL）
│   ├── grid10b/               # GRID-10B：hk(187B)、tel(88B 无魔数)（按《使用说明》V1.1）
│   ├── misc/                  # iv / vbr / lvds / app
│   └── _drafts/               # 历史草稿，不参与编译
├── generated/                 # Kaitai 生成代码（镜像 ksy/ 结构，勿手改；不入库）
├── src/                       # 应用库：Parser / Validator / Writer / Pipeline
├── scripts/
│   └── compile_ksy.py         # 一键编译 ksy/**/*.ksy -> generated/（--out 可指定目录）
├── test/                      # ★ pytest 测试 + 唯一真实样本 test/sample.hk（517×178B）
├── script/                    # 开发辅助脚本（验证/回归/体检）；_once/ 为一次性工具
├── doc/                       # ★ 文档：工程手册（含 API 协定）、Kaitai 语法说明、CRC 参考、格式说明
├── in/                        # 待解析输入（除 .gitkeep 外不入库）
├── out/                       # 解析产物（*_packets.csv / .json / .parquet；除 .gitkeep 外不入库）
├── grid_parser_ref/           # 旧解析实现 + 参考 XML（仅作版本对照）
└── xml/
    └── grid_packet.xml        # 原始包定义（存档）
```

## 工作流

### 1. 安装依赖

```powershell
pip install -r requirement.txt
```

### 2. 编写 / 修改包定义

1. 在 `ksy/` 下对应**版本子目录**编写或修改 `.ksy` 文件（Kaitai Struct 格式），
   草稿放 `ksy/_drafts/`（不参与编译）
2. 一键编译生成 Python 解析器（按子目录镜像，自动生成 `__init__.py` 包）：

```powershell
python scripts/compile_ksy.py
# 或使用 VS Code 任务：终端 -> 运行生成任务 -> 编译 Kaitai 解析器
```

### 3. 注册解析器

在 `conf/conf.json` 的 `PARSER` 数组新增一项，`MODULE` 为**包路径 + 模块名**：

```json
{
    "NAME": "grid1x_hk_parser",
    "TYPE": ".hk",                 // 匹配源文件扩展名
    "MODULE": "grid1x.grid1x_hk_packet",  // generated/ 下的包路径.模块名
    "CLASS": "Grid1xHkPacket",     // 生成的类名
    "PACKET_LEN": 187,             // 单包字节数，用于固定切片；0 表示变长包(逐包解析)
    "DESCRIPTION": "...",
    "VERSION": "1.0.0"
}
```

### 4. 运行解析

```powershell
python main.py --src .\test\sample.hk --des .\out      # --out-type csv,json,parquet 可覆盖默认
```

- 同一扩展名有多个注册解析器时，程序会列出菜单供选择（如 `.hk` 有 187B(grid1x) / 178B(yingtian) / 187B(10b) 三版，
  解析 `test/sample.hk` 请选 `grid1x_hk_178_parser`）
- 产物：`out/sample_packets.csv`（每行一包）与 `out/sample_packets.json`（结构化）
- 必须在项目根目录运行（`conf` / `generated` 走相对路径）

### 5. 运行测试

```powershell
python -m pytest test -q      # 或 VS Code 任务 “运行测试 (pytest)”
```

- 测试数据：`test/sample.hk` 是**唯一**纳入版本管理的真实样本；其余格式由 `test/_packets.py`
  在内存中按 ksy 布局合成（含正确 CRC，能覆盖“校验通过/失败”两条分支）
- `test/test_registry.py` 会检查 conf ↔ ksy ↔ generated ↔ 测试资产 是否脱节（新增解析器必须补测试）
- 详细说明见 `test/README.md`

## 各包说明（`ksy/` 下所有非草稿定义均已注册进 conf.json）

| 注册 NAME (TYPE) | 帧头 | 布局 |
|---|---|---|
| `grid1x_hk_parser` (.hk) | `0x1A2B3C4D` | 187 字节，固定（1x / XML 版） |
| `grid1x_hk_178_parser` (.hk) | `0x1A2B3C4D` | 178 字节，固定（yingtian 版；**`test/sample.hk` 即此格式**） |
| `grid10b_hk_parser` (.hk) | `0x1A2B3C4D` | 187 字节，固定（《使用说明》V1.1 全套换算） |
| `grid1x_ft_parser` (.ft) | `0x1C1C2288` | 变长：44 + `pkg_event_num`×20（事件含各自 CRC/tail） |
| `grid1x_ft_yingtian_parser` (.ft) | `0x1C1C2288` | 变长：46 + `pkg_event_num`×20（整包一个帧尾） |
| `grid1x_wf_parser` (.wf) | `0x2E2E33FF` | 568 字节（reserved@558、CRC@562、帧尾@564..568） |
| `grid1x_es_parser` (.es) | `0x3F3F44CC` | 528 字节，固定 |
| `grid11b_telemetry_parser` (.tlm) | `0x48454144` ("HEAD") | 96 字节，固定（4B HEAD + 88B 载荷 + 4B TAIL） |
| `grid10b_tel_parser` (.tel) | — | 88 字节，固定（无帧头/帧尾；与 11B 版同一份载荷） |
| `iv_parser` (.iv) | `0x29416C8E` | 404 + 8 填充 = 412 |
| `vbr_parser` (.vbr) | `0x18305B7D` | 404 + 8 填充 = 412 |
| `lvds_parser` (.lvds) | `0xEB905716` | 2048 字节，固定 |
| `app_parser` (.app) | `0x47524944` ("GRID") | 变长：18 + `data_len` + 6 |

> 同一扩展名对应多个版本时（`.hk` ×3、`.ft` ×2）由 CLI 菜单选择；`.tel` 与 `.tlm` 是同一份 88B
> 遥测载荷的两种封装（见 `doc/工程手册.md` §8）。

## 文档

| 文件 | 内容 |
|---|---|
| `doc/工程手册.md` | **主文档**：`.ksy` 语法语义、编译、取值、CRC 校验、版本矩阵、**API 协定（§12）** |
| `doc/kaitai struct说明.md` | Kaitai Struct 语法详解与踩坑（含“CRC 为什么不能写进 ksy”） |
| `doc/crc_reference.md` | CRC 参考实现、查表与标准校验值（CRC-16/XMODEM、CRC-32C） |
| `doc/housekeepping_data_format.md` | HK 遥测《使用说明》数据格式（10b 标准的字段与换算来源） |
| `ksy/README.md` | 包定义版本矩阵与写法约定（**改 ksy 前先看它**） |
| `test/README.md` | 测试说明：运行方式、覆盖矩阵、如何为新解析器补测试 |
| `CHANGELOG.md` | 版本日志（发版必须同步顶部版本号与 `conf.json` 的 `VERSION`） |

## 注意事项

- `generated/` 下代码由编译器生成，请勿手改；修改 `ksy/**.ksy` 后重新编译
- 本机 pip 版 `kaitai-struct-compiler 0.11` 不识别 `magic` 内建类型，帧头请用 `u4`
- Kaitai 字段名必须全小写（`^[a-z][a-z0-9_]*$`）；`doc` 值若含 `冒号+空格` 需加引号
- Windows 下编译器为 `.bat` 启动脚本，编译脚本已用 `shell=True` 处理
- CRC/帧头/范围等校验由 `src/validator.py` 承担（按名字以 `crc` 开头的字段自动识别）；
  算法实现可插拔，每个算法一个文件放在 `src/checks/`（`crc16_ccitt` = CRC-16/XMODEM、`crc32` = CRC-32C）；
  **算法表登记在 `conf/conf.json` 顶层 `CRC_ALGO`，与 `PARSER` 解耦**（PARSER 里不写 CRC 字段）：
  每个算法用 `SUPPORT` 声明默认适用的文件格式并按格式覆盖 `TAIL` 等；未显式指定算法时按源文件后缀
  在 `SUPPORT` 中匹配，命中即用，都没命中则不校验（也可用 `--crc-algo` 强制指定）；
  CRC 位置/跳过等参数可在 ksy 的 `instances` 里声明（`crc_skip0`/`crc_skip1`/`crc_bytes`/`crc_tail`/
  `crc_algo` …，声明后**优先于 conf**）；`.ksy` 与生成代码都不需要调试信息（不写 `ks-debug`）
- CRC 参考实现与查表见 `doc/crc_reference.md`（已复核 256/256）
- 物理量换算（单位/比例）在 `.ksy` 中用参数化类型 + `instances` 实现，raw 与 converted 并存
  （见 `ksy/grid10b/grid10b_tel_packet.ksy` 与 `doc/工程手册.md` §4.5）
- 外部应用请按 `doc/工程手册.md` **§12 API 协定** 调用（`Pipeline` 是推荐入口；`generated/` 不是接口）
