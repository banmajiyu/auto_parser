"""CRC-32C —— 适用于 IV / VBR 数据。

对应《使用说明》附 1 的 `crc32()`：

    crc = 0xFFFFFFFF;
    while (length--) crc = crc_tab[(crc ^ *data++) & 0xFF] ^ (crc >> 8);
    return crc ^ 0xFFFFFFFF;

即：多项式 `0x1EDC6F41`（反射式写法 `0x82F63B78`）、初值 `0xFFFFFFFF`、
反射输入/输出、最终异或 `0xFFFFFFFF` —— 标准名 **CRC-32C / CRC-32/ISCSI**。

校验值：`crc32(b"123456789") == 0xE3069283`。

⚠️ 这**不是** zlib / 以太网用的 CRC-32（多项式 `0x04C11DB7`，校验值 `0xCBF43926`），
两者结果完全不同，不要用 `zlib.crc32` 代替。

查表由多项式按位生成（`_build_table`），已与附 1 的表逐项比对一致（256/256）。
本文件不做任何“注册”：算法表在 `conf/conf.json` 顶层 `CRC_ALGO` 中声明。
"""

_POLY_REFLECTED = 0x82F63B78   # bit-reverse(0x1EDC6F41)，反射式实现用


def _build_table(poly: int = _POLY_REFLECTED, n: int = 256) -> tuple:
    """按“反射式”约定生成 8bit 查表（table[i] 为字节 i 的 8 次移位结果）。"""
    table = []
    for i in range(n):
        crc = i
        for _ in range(8):
            crc = (crc >> 1) ^ poly if crc & 1 else crc >> 1
        table.append(crc & 0xFFFFFFFF)
    return tuple(table)


_TABLE = _build_table()


def crc32(data: bytes, init: int = 0xFFFFFFFF) -> int:
    """CRC-32C（poly 0x1EDC6F41，init/xorout 0xFFFFFFFF）。"""
    crc = init & 0xFFFFFFFF
    for b in data:
        crc = _TABLE[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return (crc ^ 0xFFFFFFFF) & 0xFFFFFFFF
