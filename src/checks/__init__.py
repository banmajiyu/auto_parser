"""CRC 算法实现包（纯计算，每个算法一个文件）。

本包**不含任何注册逻辑**：可用算法表写在 `conf/conf.json` 的顶层 `CRC_ALGO` 数组里，
`src/validator.py` 负责按名字从 conf 查表并动态导入 `MODULE.FUNC`。

- `crc16_ccitt.py` → CRC-16/XMODEM（HK 文件、科学数据文件）
- `crc32.py`       → CRC-32C（IV / VBR 数据）

新增算法：
1. 在 `src/checks/` 下加一个模块，实现 `func(data: bytes, init: int) -> int`；
2. 在 `conf/conf.json` 的 `CRC_ALGO` 数组里登记一条：
   `{"NAME": ..., "MODULE": "src.checks.<模块>", "FUNC": "<函数>",
     "SIZE": ..., "INIT": ..., "BYTEORDER": ..., "DESCRIPTION": ...}`；
3. 解析器条目用 `"CRC_ALGO": "<NAME>"` 引用即可，Validator / Pipeline 无需改动。
"""
