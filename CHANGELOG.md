# 更新日志

## v0.2 2026-09-13

### 描述

- 在 v0.1 基础上完成“**定义 — 解析 — 校验 — 输出**”四段解耦：`ksy/` 成为唯一真源，
  应用层收敛到 `src/` 四件套（`Parser` / `Validator` / `Writer` / `Pipeline`），
  并补齐测试、辅助脚本与文档目录，具备对外提供接口（API 协定）的条件。

### 新增

- **应用层重构**：解析逻辑从 `main.py` 拆到 `src/` —— `parser.py`（切片解析/字段提取）、
  `validator.py`（CRC 语义校验）、`writer.py`（CSV/JSON/Parquet 落盘）、`pipeline.py`（串起三件套）；
  `main.py` 退化为薄 CLI（参数/conf/解析器选择）
- **CRC 校验可插拔且与解析器解耦**：算法实现放 `src/checks/`（`crc16_ccitt` = CRC-16/XMODEM、
  `crc32` = CRC-32C），算法表登记在 `conf/conf.json` 顶层 `CRC_ALGO`，每个算法用 `SUPPORT`
  声明默认适用的文件格式（可按格式覆盖 `TAIL`/`SIZE`/`INIT`/`BYTEORDER`/`DROP_ON_FAIL`），
  `PARSER` 条目里不再出现任何 CRC 字段；ksy 也可用 `instances` 声明
  `crc_skip0`/`crc_skip1`/`crc_bytes`/`crc_tail`/`crc_algo` 等元数据（优先于 conf）
- **输出支持 Parquet**（`Writer.SUPPORTED` 为能力唯一真源，`pyarrow` 惰性导入）；`conf` 的
  `OUTPUT_TYPE` 控制默认格式，`--out-type` 可临时覆盖，置 `[]` 则只解析不写文件
- **`ksy/` 成为唯一真源**：把原 `spec/**` 重写为更完整的 Kaitai 定义并入 `ksy/`，按**版本**分目录
  （`grid1x/`、`grid11b/`、`grid10b/`、`misc/`），原 `spec/` 目录删除；`scripts/compile_ksy.py`
  改为扫描 `ksy/`（新增 `--out`，自动跳过 `_drafts/` 与 `*_draft.ksy`），`generated/` 镜像 `ksy/` 树
- **新增版本定义**：`grid1x_hk_packet_178.ksy`（178B）、`grid1x_ft_packet_yingtian.ksy`（FT yingtian 版）；
  `wave.ksy` 改名 `_drafts/grid10b_tel_draft.ksy`，原 528B 的 FT 草稿移入 `_drafts/`
- **测试体系**：新增 `test/`（pytest），覆盖全部解析器（合成包）+ 真实样本 + 流水线/落盘 +
  注册表一致性；唯一真实样本 `test/sample.hk`（517×178B）随仓库提交；`requirement.txt` 增加 `pytest`
- **注册全部解析器**：`ksy/` 下所有非草稿定义都写进 `conf.json` 的 `PARSER`（新增 178B HK、10b HK、
  FT yingtian、10b 遥测 `.tel` 四条）；同一扩展名的多个版本（`.hk` ×3、`.ft` ×2）由 CLI 菜单选择
- **文档目录**：新建 `doc/`（工程手册 / Kaitai 语法说明 / CRC 参考 / HK 格式说明 / yingtian 包文本 /
  历史 notebook）；工程手册新增 **§12 API 协定**（稳定面、异常、数据表示、CLI 与配置契约）
- **辅助脚本整理**：`dev/` 更名 `script/`，仍在用的验证脚本留在根级，一次性工具移入 `script/_once/`；
  README 与工程手册、`ksy/README.md` 均补充其用途说明

### 变更

- 全部 ksy 改为**单包写法**（去掉 `frames: repeat: eos` 的 frameseq）：`Parser` 按 `PACKET_LEN` 切片即可、
  输出不再多一层 `frames`；`meta.id` 唯一化（`grid10b_hk_packet` / `grid10b_tel_packet` / `grid1x_*`）
- 用上更多 ksy 语法：`contents` 强校验魔数、`enums` 取值表、参数化类型 `scaled_u2`（raw/converted 并存）、
  `instances` 里的 CRC 元数据与 `body_data` 字节视图
- 输出表示有意变化：魔数字段变为**十六进制串**；带换算的字段变为 `{"raw":…, "converted":…}`；
  HK 字段改用 10b 命名（列数与顺序不变）；`iv/vbr` 的 `padding` 改名 `reserved`，`wf` 新增中间 `reserved`
- 目录重组：`in/` 只保留本地输入（真实样本 `sample.hk` 移入 `test/`），`generated/` 不入库，
  测试 / 脚本 / 文档各归其位（`test/`、`script/`、`doc/`）

### 修复

- **WF 尾部 2 字节错位**：2 字节占位应在 558..560（不是包尾），CRC@562、帧尾@564..568，
  `crc_tail` 由 8 改为 6（两份参考 XML + 旧定帧正则三重印证）。修前真实 WF 包 CRC 永远校验不过
  （整包被丢），修后可通过；`conf.json` 里 `.wf` 的 `TAIL` 同步改为 6
- **坏包不再中断整文件**：`contents` 强校验上线后，错位/坏包会抛异常；`Parser` 改为跳过无法解析的包并
  计入 `unparsed`（`main.py` 打印警示，`Pipeline.run()` 返回值新增 `unparsed`）
- 修正 `vbr_packet.ksy` 旧稿的两个问题：`doc` 缩进导致的 YAML 语法错误、帧头魔数 `0x7b` → `0x7d`
- 修正旧 `iv_packet.ksy` 缺 8 字节导致 `repeat: eos` 错位的问题（现为 `4 + 200×u2 + reserved(8)`）
- 修复 `main.py` 的命名问题、索引边界与列表处理错误，以及 `conf.json` 的版本号错误

### 测试与验证

- `test/sample.hk`（517×178B）用 `grid1x_hk_packet_178` 解析：`packets=517 unparsed=0`，
  **CRC 校验 checked=517 / dropped=0**
- pytest 全套：`python -m pytest test -q`（逐格式合成包、CRC 正/反例、变长包、流水线/落盘、注册表一致性）
- 回归对比（`script/compare_generated.py`）：迁移前后解析器对同一合成包逐字段比对，
  `hk/ft/es/tlm/hk10b/tel10b/iv/vbr/lvds/app` **值全部一致**；唯一值差异就是上面 WF 的修正
- 布局体检（`script/verify_ksy_drafts.py`）：各 ksy 与对应参考 XML 的字段边界逐字节对齐
- 旧实现等价性（`script/verify_equiv.py`）：HK/ES 的 CRC 语义与旧 `parse_grid_data` 完全等效；
  WF 修后与旧 XML 规则一致

### 注意

- **破坏性变更**：`spec/` 目录不复存在（定义统一在 `ksy/`）；输出表示变化（魔数→十六进制串、
  换算字段→`{raw, converted}`、`iv/vbr` 的 `padding`→`reserved`）。外部调用请以
  `doc/工程手册.md` **§12 API 协定**为准
- CRC 校验从“从未真正生效”（生成解析器不带 `_debug` 导致跳过）变为**生效**；无真实 CRC 的合成样本
  （如本地 `in/sample.ft`）会被丢弃，排查时用 `"DROP_ON_FAIL": false` 或 `--crc-algo`
- ksy 与生成代码都**不需要**调试信息（不写 `ks-debug`）：CRC 位置改由 ksy `instances` 元数据 + conf
  驱动，`src/validator.py` 不再依赖 `_debug`
- 未实现项（两版参考 XML 都未定义/旧代码也未实现）：`lvds`/`app` 的 `check_sum`（XOR 语义）、
  `iv`/`vbr` 尾部的 CRC-32C（conf 里 crc32 的 `SUPPORT` 含 `.iv`/`.vbr`，但 ksy 无 `crc` 字段 → 不会触发）
- `DROP_ON_FAIL: false` 只是“保留坏包并照常写出”，此时 `dropped` 仍为 0（它统计的是真正被丢弃的包数）
- `test/sample.hk` 用 187 版解析器读会跳过 489 个包并提示版本不匹配
  （按 `doc/工程手册.md` §11.5 注册 178 版即可正确解析）

## v0.1 2026-09-01

### 描述

- 首个测试版本
- 一个用于解析天格卫星下行数据包的工具，为解决现有解析工具不统一的问题而诞生。一个基本思路是，借助AI将xml文件翻译为kaitai struct文件，然后借助kaitai struct compiler自动生成解析器完成解析。
- 目前解析器已经在一些示例文件上跑通。
- 目前通过命令行方式使用程序，可能以后将扩展更多命令

###  存在的问题

- 自动生成的解析器只能直接提取字段，校验等工作无法胜任，所以需要考虑在应用层做校验。
- 测试中只有sample.hk使用了真实数据，其他测试使用的是合成数据，可靠性需要进一步验证
- 该工具目前较独立，还没有考虑与其他应用协作或提供接口，如天格载荷上位机应用