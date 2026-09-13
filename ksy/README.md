# ksy/ —— Kaitai 包定义（唯一真源）

本目录是**唯一真源**：`scripts/compile_ksy.py` 扫描 `ksy/**/*.ksy` 并镜像输出到 `generated/`。
（历史的 `spec/` 已删除；`generated/` 是产物，勿手改。）

```powershell
python scripts/compile_ksy.py                  # -> generated/（conf.json 的 MODULE 路径不变）
python scripts/compile_ksy.py --out .\tmp\gen  # 编译到临时目录（做迁移/改动对比时用）
```

## 目录与版本

| 路径 | 版本 / 来源 | 说明 |
|---|---|---|
| `grid1x/grid1x_hk_packet.ksy` | 1x（`xml/grid_packet.xml`） | 187B；conf 注册为 `grid1x_hk_parser`（`.hk`，同后缀另有 178B / 10b 两版）；换算只按 XML tag（仅 SiPM 三处） |
| `grid1x/grid1x_hk_packet_178.ksy` | yingtian（`grid_parser_ref/yingtian_packet.xml`） | 178B；`test/sample.hk` 实测 CRC 517/517 通过；与 187 版字段集不同 |
| `grid1x/grid1x_ft_packet.ksy` | grid | 变长 `44 + N×20`；每事件含自己的 crc + 帧尾 0xCC118822 |
| `grid1x/grid1x_ft_packet_yingtian.ksy` | yingtian | 584B（N=27）；每事件 18B 数据（u8 时间戳），末尾单个 crc + 帧尾 |
| `grid1x/grid1x_wf_packet.ksy` | grid + yingtian 交叉核对 | 568B；**含 558..560 的 2 字节 reserved**，CRC@562、帧尾@564..568 |
| `grid1x/grid1x_es_packet.ksy` | 两版一致 | 528B；CRC@522 |
| `grid11b/grid11b_telemetry_packet.ksy` | 11B（XML） | 96B = 4B "HEAD" + 88B 载荷 + 4B "TAIL"；conf 注册的 `.tlm` |
| `grid10b/grid10b_hk_packet.ksy` | 10b（《使用说明》V1.1） | 187B；使用说明的全套换算（ADC 用 s2、GPS/四元数用 s4） |
| `grid10b/grid10b_tel_packet.ksy` | 10b（《使用说明》V1.1） | 88B，**无魔数**（CAN 拆分载荷）；与 11B 版载荷逐字节相同 |
| `misc/iv_packet.ksy`、`misc/vbr_packet.ksy` | 两版一致 | 412B = 4 + 200×u2 + 8B 未定义 |
| `misc/lvds_packet.ksy` | 仅 XML | 2048B；`check_sum` 为 XOR 语义（未实现校验） |
| `misc/app_packet.ksy` | 两版一致 | 变长 `18 + data_len + 6`；`check_sum` 为 XOR 语义（未实现校验） |
| `_drafts/` | 历史草稿 | **不参与编译**（`compile_ksy.py` 跳过 `_` 开头目录与 `*_draft.ksy`） |

> ⚠️ 同名文件很容易混淆，改之前先看 `meta.id` 与文件头 `doc` 的"版本与用法"一节。
> 详细对照（含 tel 10b↔11B 的逐字段映射、FT 两版差异）见各文件 `doc` 与 `doc/工程手册.md` §11。
>
> 本目录下**所有非草稿定义都已在 `conf/conf.json` 注册**（同一扩展名的多个版本由 CLI 菜单区分：
> `.hk` ×3、`.ft` ×2；88B 无魔数遥测用 `.tel`、96B HEAD/TAIL 版用 `.tlm`）。

## 写法约定

1. **单包写法**：根 `seq` 直接就是包字段，不使用 `frames: repeat: eos` 的 frameseq。
   - 原因：`Parser` 按 `PACKET_LEN` 切片（变长包按 `io.pos()` 推进），frameseq 会一次吃完整个流，
     且输出会多一层 `frames` 嵌套。
2. **魔数字段用 `contents`**（强校验）。注意：字段会变成 `bytes`，输出是十六进制串；
   且 `contents` 不能与 `type` 同时写。
3. **单位换算用参数化类型**：`types.scaled_u2`（`params: scale/offset` + `instances.converted`），
   字段写作 `type: scaled_u2(1.25, 0.0)` → 输出 `{"raw":…, "converted":…}` 且 raw 原值不丢。
4. **CRC 元数据写在 `instances`**（`crc_skip0/crc_skip1/crc_bytes/crc_tail/crc_algo/…`），
   `src/validator.py` 会自动读取，优先级高于 conf 的 `SUPPORT`；有 `crc*` 字段但**没写元数据**时用 conf。
5. **枚举**用顶层 `enums:`（键可写十六进制 `0x55`），字段加 `enum: <名>`。
6. `doc` 的值内含"冒号+空格"时必须加引号（YAML 语法），如 `doc: "源 XML: multi=1"`。
7. 改完**务必编译一次**（见上）；`.ksy` 的 YAML/键名问题只在编译时暴露。

## 相关脚本（script/）与测试（test/）

| 路径 | 作用 |
|---|---|
| `script/verify_ksy_drafts.py` | 把 ksy 的字段布局与参考 XML 按字节边界对撞（版本/偏移是否一致） |
| `script/compare_generated.py` | 同一合成包用"改动前/后"的解析器各解析一遍，逐叶子字段回归对比 |
| `script/verify_equiv.py` | 旧 `grid_parser_ref` 解析函数 vs 现 `Parser`/`Validator` 的等价性实测（含 CRC 用例） |
| `script/verify_e2e.py` | 端到端：178B HK 全量 CRC + WF 布局修正对照 |
| `script/_once/` | 一次性工具：`flatten_frameseq.py`（frameseq → 单包）、`dump_ref_xml.py`（dump 参考 XML 布局） |
| `test/` | pytest 测试（`python -m pytest test -q`）：逐格式合成包 + 真实样本 + 注册表一致性，见 `test/README.md` |
