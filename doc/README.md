# doc/ —— 文档资料

本目录集中存放项目文档（源码与配置仍在仓库根目录：`ksy/`、`src/`、`conf/`、`script/`、`test/`）。

| 文件 | 说明 | 主要读者 |
|---|---|---|
| `工程手册.md` | **主文档**：`.ksy` 语法语义、编译、取值、CRC 校验、版本矩阵、API 协定（§12） | 维护者 + 二次开发者 |
| `kaitai struct说明.md` | Kaitai Struct 语法详解与踩坑（含“为什么 CRC 不能写进 ksy” §8） | 写/改 ksy 的人 |
| `crc_reference.md` | CRC 参考实现、查表与标准校验值（CRC-16/XMODEM、CRC-32C） | 校验逻辑维护者 |
| `housekeepping_data_format.md` | HK 遥测《使用说明》数据格式（10b 标准的字段与换算来源） | 校对 HK 定义的人 |
| `yingtian_pkt.txt` | yingtian 版包定义的原始文本记录 | 版本追溯 |
| `test.ipynb` | 早期手工调试 notebook（**历史草稿**，路径按当时目录写成，仅供参考） | 版本追溯 |

> 相关入口：仓库根 `README.md`（快速入门）、`CHANGELOG.md`（版本日志）、`ksy/README.md`（包定义版本矩阵）、
> `test/README.md`（测试说明）、`script/`（开发辅助脚本）。
