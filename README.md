# AUTO PARSER

基于 [Kaitai Struct](https://kaitai.io) 的配置化数据包解析工具。包结构定义在 `spec/*.ksy` 中，由 Kaitai 编译器生成 Python 解析器到 `generated/`，再通过 `main.py` 按配置注册的解析器对源文件进行切片解析，输出 CSV / JSON。

## 目录结构

```
auto_parser/
├── main.py                    # 入口：选择解析器 -> 切片解析 -> 输出 CSV/JSON
├── requirement.txt            # 依赖清单
├── README.md                  # 本文档
├── .gitignore
├── .vscode/
│   ├── tasks.json             # 编译 / 运行 任务
│   └── settings.json          # 解释器与 extraPaths 配置
├── conf/
│   └── conf.json              # 解析器注册表（NAME/TYPE/MODULE/CLASS/PACKET_LEN）
├── in/                        # 待解析源文件（如 sample.hk）
├── out/                       # 解析产物（*_packets.csv / *_packets.json）
├── spec/                      # Kaitai 定义 (.ksy)，按设备分组
│   ├── grid1x/                # GRID-1X 系列
│   │   ├── grid1x_hk_packet.ksy
│   │   ├── grid1x_ft_packet.ksy
│   │   ├── grid1x_wf_packet.ksy
│   │   └── grid1x_es_packet.ksy
│   ├── grid11b/               # GRID-11B 系列
│   │   └── grid11b_telemetry_packet.ksy
│   └── misc/                  # 杂项/独立格式
│       ├── iv_packet.ksy
│       ├── vbr_packet.ksy
│       ├── lvds_packet.ksy
│       └── app_packet.ksy
├── generated/                 # Kaitai 生成代码（镜像 spec/ 结构，勿手改）
├── scripts/
│   └── compile_ksy.py         # 一键编译 spec/*.ksy -> generated/
├── src/                       # （预留）应用库代码
└── xml/
    └── grid_packet.xml        # 原始包定义（存档）
```

## 工作流

### 1. 安装依赖

```powershell
pip install -r requirement.txt
```

### 2. 编写 / 修改包定义

1. 在 `spec/` 下对应设备子目录编写或修改 `.ksy` 文件（Kaitai Struct 格式）
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
python main.py --src .\in\sample.hk --des .\out
```

- 同一扩展名有多个注册解析器时，程序会列出菜单供选择
- 产物：`out/sample_packets.csv`（每行一包）与 `out/sample_packets.json`（结构化）

## 各包说明（均已注册进 conf.json）

| 注册 NAME (TYPE) | 帧头 | 布局 |
|---|---|---|
| `grid1x_hk_parser` (.hk) | `0x1A2B3C4D` | 187 字节，固定 |
| `grid1x_ft_parser` (.ft) | `0x1C1C2288` | 变长：44 + `pkg_event_num`×20（事件含各自 CRC/tail） |
| `grid1x_wf_parser` (.wf) | `0x2E2E33FF` | 568 字节（尾部 vary_wf 基址 540，末尾 2 字节填充） |
| `grid1x_es_parser` (.es) | `0x3F3F44CC` | 528 字节，固定 |
| `grid11b_telemetry_parser` (.tlm) | `0x48454144` ("HEAD") | 96 字节，固定 |
| `iv_parser` (.iv) | `0x29416C8E` | 404 + 8 填充 = 412 |
| `vbr_parser` (.vbr) | `0x18305B7D` | 404 + 8 填充 = 412 |
| `lvds_parser` (.lvds) | `0xEB905716` | 2048 字节，固定 |
| `app_parser` (.app) | `0x47524944` ("GRID") | 变长：18 + `data_len` + 6 |

## 注意事项

- `generated/` 下代码由编译器生成，请勿手改；修改 `spec/*.ksy` 后重新编译
- 本机 pip 版 `kaitai-struct-compiler 0.11` 不识别 `magic` 内建类型，帧头请用 `u4`
- Kaitai 字段名必须全小写（`^[a-z][a-z0-9_]*$`）；`doc` 值若含 `冒号+空格` 需加引号
- Windows 下编译器为 `.bat` 启动脚本，编译脚本已用 `shell=True` 处理
- CRC/帧头校验、物理量换算等逻辑未实现，需在应用层补充
