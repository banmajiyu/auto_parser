# -*- coding: utf-8 -*-
"""测试用的“合成包”构建工具与格式清单（非测试用例，pytest 不会收集本文件）。

为什么在内存里合成包：
    `in/` 目录除 `.gitkeep` 外都被 `.gitignore` 忽略（只保留本地输入样本），
    因此测试不能依赖 `in/sample.*`；纳入版本管理的真实数据只有 `test/sample.hk`。
    这里按各 `.ksy` 的字段布局在内存中合成**合法**包：帧头/帧尾写真实魔数（`contents` 强校验），
    CRC 按 ksy `instances` 声明的位置写入 —— 这样解析与校验都能走到“通过”分支。

布局来源（改 ksy 后若布局变化，本文件的常量必须同步）：
    - 定长格式见 `doc/工程手册.md` §11.2 版本矩阵与 `ksy/README.md`；
    - FT / APP 为变长，公式写在各自 builder 的 docstring 里。
"""
from __future__ import annotations

from dataclasses import dataclass

from src.checks.crc16_ccitt import crc16_ccitt

# --- FT 两版共用的帧头/帧尾魔数 ---
FT_MAGIC = bytes.fromhex("1c1c2288")
FT_TAIL = bytes.fromhex("cc118822")


def pseudo_bytes(n: int) -> bytearray:
    """确定性伪随机字节。

    刻意避开全 0：CRC 的 init=0、异或/初值都为 0 时，全 0 数据的校验值恒为 0，
    用全 0 数据做用例会掩盖“位置/初值配错”的问题。
    """
    return bytearray((i * 7 + 3) & 0xFF for i in range(n))


@dataclass(frozen=True)
class PacketSpec:
    """一个**定长**格式的合成参数（全部取自对应 `.ksy`）。"""

    key: str                       # 测试 id
    module: str                    # generated/ 下的模块路径（包路径.模块名）
    cls: str                       # 生成的类名
    ext: str                       # 源文件后缀（决定 CRC 算法按 SUPPORT 匹配）
    plen: int                      # 帧长（字节）
    magic: bytes = b""             # 帧头（ksy 用 contents 强校验，空 = 无帧头，如 10b 遥测）
    crc_at: int = -1               # CRC 字段起点；-1 = 该格式无 CRC 字段
    tail_at: int = -1              # 帧尾起点；-1 = 无帧尾
    tail: bytes = b""
    registered: bool = True        # 是否已在 conf.json 注册（当前全部已注册）

    @property
    def has_crc(self) -> bool:
        return self.crc_at >= 0


FIXED_SPECS: tuple[PacketSpec, ...] = (
    PacketSpec("grid1x_hk", "grid1x.grid1x_hk_packet", "Grid1xHkPacket", ".hk", 187,
               magic=bytes.fromhex("1a2b3c4d"), crc_at=185),
    PacketSpec("grid1x_hk_178", "grid1x.grid1x_hk_packet_178", "Grid1xHkPacket178", ".hk", 178,
               magic=bytes.fromhex("1a2b3c4d"), crc_at=176),
    PacketSpec("grid10b_hk", "grid10b.grid10b_hk_packet", "Grid10bHkPacket", ".hk", 187,
               magic=bytes.fromhex("1a2b3c4d"), crc_at=185),
    PacketSpec("grid1x_es", "grid1x.grid1x_es_packet", "Grid1xEsPacket", ".es", 528,
               magic=bytes.fromhex("3f3f44cc"), crc_at=522,
               tail_at=524, tail=bytes.fromhex("33ffcc44")),
    PacketSpec("grid1x_wf", "grid1x.grid1x_wf_packet", "Grid1xWfPacket", ".wf", 568,
               magic=bytes.fromhex("2e2e33ff"), crc_at=562,
               tail_at=564, tail=bytes.fromhex("22eeff33")),
    PacketSpec("grid11b_telemetry", "grid11b.grid11b_telemetry_packet",
               "Grid11bTelemetryPacket", ".tlm", 96,
               magic=b"HEAD", tail_at=92, tail=b"TAIL"),
    PacketSpec("grid10b_tel", "grid10b.grid10b_tel_packet", "Grid10bTelPacket", ".tel", 88),
    PacketSpec("iv", "misc.iv_packet", "IvPacket", ".iv", 412,
               magic=bytes.fromhex("29416c8e")),
    PacketSpec("vbr", "misc.vbr_packet", "VbrPacket", ".vbr", 412,
               magic=bytes.fromhex("18305b7d")),
    PacketSpec("lvds", "misc.lvds_packet", "LvdsPacket", ".lvds", 2048,
               magic=bytes.fromhex("eb905716"), tail_at=2044,
               tail=bytes.fromhex("10bd59bf")),
)

FIXED_IDS: list[str] = [spec.key for spec in FIXED_SPECS]
CRC_SPECS: tuple[PacketSpec, ...] = tuple(s for s in FIXED_SPECS if s.has_crc)
NO_CRC_SPECS: tuple[PacketSpec, ...] = tuple(s for s in FIXED_SPECS if not s.has_crc)

# --- 变长格式的 Parser 入口（PACKET_LEN=0 表示逐包解析） ---
FT_ENTRY = {"NAME": "grid1x_ft_parser", "TYPE": ".ft",
            "MODULE": "grid1x.grid1x_ft_packet", "CLASS": "Grid1xFtPacket", "PACKET_LEN": 0}
FT_YINGTIAN_ENTRY = {"NAME": "grid1x_ft_yingtian_parser", "TYPE": ".ft",
                     "MODULE": "grid1x.grid1x_ft_packet_yingtian",
                     "CLASS": "Grid1xFtPacketYingtian", "PACKET_LEN": 0}
APP_ENTRY = {"NAME": "app_parser", "TYPE": ".app",
             "MODULE": "misc.app_packet", "CLASS": "AppPacket", "PACKET_LEN": 0}


def entry_for(spec: PacketSpec) -> dict:
    """由 PacketSpec 造一个 Parser 入口（与 conf 是否注册无关）。"""
    return {"NAME": spec.key, "TYPE": spec.ext, "MODULE": spec.module,
            "CLASS": spec.cls, "PACKET_LEN": spec.plen}


def build_fixed(spec: PacketSpec) -> bytes:
    """合成一个合法的定长包：魔数 + 伪随机载荷 + 帧尾（如有）+ 正确的 CRC16（如有）。"""
    buf = pseudo_bytes(spec.plen)
    if spec.magic:
        buf[0:len(spec.magic)] = spec.magic
    if spec.tail_at >= 0:
        buf[spec.tail_at:spec.tail_at + len(spec.tail)] = spec.tail
    if spec.has_crc:
        crc = crc16_ccitt(bytes(buf[:spec.crc_at]))       # skip0 = skip1 = 0
        buf[spec.crc_at:spec.crc_at + 2] = crc.to_bytes(2, "big")
    return bytes(buf)


def build_ft(n_events: int) -> bytes:
    """grid 版 FT：`44 + N*20` 字节；每事件 = 14B 数据 + crc(u2) + 帧尾 0xCC118822。

    `pkg_event_num` 位于包头偏移 34..36（header 4 + utc 4 + pps 4 + ts_pps 8 + ts_bf 8
    + channel 2 + event_number 4 = 34），末尾事件的 crc 在包尾前 6 字节（crc_tail = 6）。
    """
    plen = 44 + n_events * 20
    buf = pseudo_bytes(plen)
    buf[0:4] = FT_MAGIC
    buf[34:36] = n_events.to_bytes(2, "big")
    for i in range(n_events):
        start = 44 + i * 20
        buf[start + 16:start + 20] = FT_TAIL          # 事件尾（contents 强校验）
    crc = crc16_ccitt(bytes(buf[:plen - 6]))
    buf[plen - 6:plen - 4] = crc.to_bytes(2, "big")
    return bytes(buf)


def build_ft_yingtian(n_events: int) -> bytes:
    """yingtian 版 FT：`46 + N*20` 字节（40B 包头 + N×20B 事件 + crc + 帧尾）。

    与 grid 版的差别：包头 40B（无 timestamp_bf，多 4B reserved）、事件步长同为 20B
    但内部是 18B 数据 + 2B 占位、整包只有**一个**帧尾（在包尾）。
    `pkg_event_num` 位于包头偏移 26..28。
    """
    plen = 46 + n_events * 20
    buf = pseudo_bytes(plen)
    buf[0:4] = FT_MAGIC
    buf[26:28] = n_events.to_bytes(2, "big")
    buf[plen - 4:plen] = FT_TAIL
    crc = crc16_ccitt(bytes(buf[:plen - 6]))
    buf[plen - 6:plen - 4] = crc.to_bytes(2, "big")
    return bytes(buf)


def build_app(data_len: int) -> bytes:
    """APP：`18 + data_len + 6` 字节（18B 头 + data_len 字节数据 + check_sum(u2) + tail(u4)）。

    `data_len` 位于包头偏移 14..18（header 4 + frame_id 4 + total_frame 4 + frame_type 1
    + file_num 1），`data` 字段用 `size: data_len` 读变长体。
    """
    plen = 18 + data_len + 6
    buf = pseudo_bytes(plen)
    buf[0:4] = bytes.fromhex("47524944")              # "GRID"
    buf[14:18] = data_len.to_bytes(4, "big")
    return bytes(buf)


def flip_byte(data: bytes, offset: int) -> bytes:
    """把指定偏移的字节取反（用于制造 CRC 失败 / 破坏魔数）。"""
    buf = bytearray(data)
    buf[offset] ^= 0xFF
    return bytes(buf)
