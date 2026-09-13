# test/ —— 解析器测试

`test/` 是本仓库的 **pytest 测试目录**，也是**唯一**纳入版本管理的测试数据所在地
（`in/` 只放本地待解析输入、不入库；`test/sample.hk` 是唯一的真实样本）。

## 运行

```powershell
python scripts/compile_ksy.py      # 1) 先编译（generated/ 不入库，测试与主程序都依赖它）
python -m pytest test -q           # 2) 必须在项目根目录运行
python -m pytest test -q -k hk     # 只跑 HK 相关用例
python -m pytest test -q --collect-only   # 只看用例清单
```

> 必须在**项目根**运行：`src/parser.py`、`src/validator.py` 里的 conf / generated 路径是相对路径。
> `.vscode/tasks.json` 里有现成任务 “运行测试 (pytest)”（可先跑 “编译 Kaitai 解析器”）。

## 文件

| 文件 | 内容 |
|---|---|
| `conftest.py` | 全局夹具：导入路径、工作目录、临时文件写出；导出 conf 注册表 `ENTRIES` |
| `_packets.py` | **合成包工具**（非用例）：格式布局表 `FIXED_SPECS` + FT/APP 变长包 builder |
| `test_parsers.py` | 全部格式的解析冒烟测试：帧长/字段/帧头帧尾、坏包跳过、变长包推进 |
| `test_crc.py` | CRC 算法标准值、conf `SUPPORT` 策略匹配、包级校验与丢弃行为 |
| `test_sample_hk.py` | 真实样本 `sample.hk`（517×178B）：解析 + CRC 全通过 + 与 187B 版的差异 |
| `test_pipeline_writer.py` | `Pipeline` 结果契约、`output_type=[]`、CSV/JSON/Parquet 产物、`main.run()` |
| `test_registry.py` | conf ↔ ksy ↔ generated ↔ 测试资产 的一致性（防漏测/漏编译/版本号不同步） |

> 下表所有格式均已在 `conf/conf.json` 注册；同一扩展名有多个版本时（`.hk` ×3、`.ft` ×2）由 CLI 菜单选择。

## 覆盖矩阵

| 格式（ksy） | 帧长 | 测试来源 |
|---|---|---|
| `grid1x_hk_packet` | 187 | 合成包 + `test_crc` |
| `grid1x_hk_packet_178` | 178 | 合成包 + **真实样本** `test/sample.hk` |
| `grid10b_hk_packet` | 187 | 合成包 + `test_crc` |
| `grid1x_ft_packet` | `44+N×20` | 变长 builder（1/2/3/5 事件、多包同文件、残包） |
| `grid1x_ft_packet_yingtian` | `46+N×20` | 变长 builder + `test_crc` |
| `grid1x_wf_packet` | 568 | 合成包 + `test_crc`（含 ksy 元数据优先级） |
| `grid1x_es_packet` | 528 | 合成包 + `test_crc`（混合好/坏包） |
| `grid11b_telemetry_packet` | 96 | 合成包（无 crc 字段 → 校验跳过） |
| `grid10b_tel_packet` | 88 | 合成包（无魔数/无 crc） |
| `misc/iv_packet`、`vbr_packet` | 412 | 合成包（`SUPPORT` 命中 crc32 但无 crc 字段 → 跳过） |
| `misc/lvds_packet` | 2048 | 合成包 |
| `misc/app_packet` | `18+D+6` | 变长 builder（D=0/16/64） |

## 为什么用“合成包”

- `in/` 除 `.gitkeep` 外全部被 `.gitignore` 忽略，测试不能依赖它；
- 合成包可精确控制 **帧头/帧尾魔数** 与 **CRC 位置**，从而同时覆盖“校验通过”和“校验失败”两条分支；
- 造数据时用确定性伪随机字节（`pseudo_bytes`）而非全 0：CRC 在 `init=0` 时对全 0 数据恒为 0，会掩盖配错。

## 新增解析器 / 修改 ksy 后

1. 在 `test/_packets.py` 登记布局（定长 → `FIXED_SPECS`；变长 → 写 builder + 入口常量）；
2. 若注册进 `conf/conf.json`，`test_registry.py` 会自动检查 `MODULE/CLASS/PACKET_LEN` 与布局表一致；
3. 运行 `python -m pytest test -q`。**没登记测试资产的解析器会让 `test_registry.py` 失败**，这是刻意设计（防漏测）。
