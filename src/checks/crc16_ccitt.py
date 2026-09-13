"""CRC-16/XMODEM —— 适用于 HK 文件、科学数据文件。

对应《使用说明》附 1 的 `star::util::Crc16`：多项式 `0x1021`、初值 `0x0000`、
MSB-first、无反射、无最终异或，即 CRC-16/XMODEM。

校验值：`crc16_ccitt(b"123456789") == 0x31C3`（与附 1 参考实现一致）。

注：本函数原样迁移自 `src/validator.py`（函数名、签名、行为均未改动），
`src/validator.py` 仍会把它 re-export 出来，历史调用方无需修改。
本文件不做任何“注册”：算法表在 `conf/conf.json` 顶层 `CRC_ALGO` 中声明。
"""


def crc16_ccitt(data: bytes, init: int = 0) -> int:
    """CRC-16/CCITT implementation (poly 0x1021)."""
    crc = init & 0xFFFF
    for b in data:
        crc ^= (b << 8) & 0xFFFF
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc
