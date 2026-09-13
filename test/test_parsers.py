# -*- coding: utf-8 -*-
"""全部解析器的解析测试（合成包，逐格式覆盖）。

覆盖点：
  1. 每个 ksy 定义的解析器都能解析一包合法数据（帧长 / 字段 / trailing / raw_chunks）；
  2. 帧头（`contents`）不匹配 -> 该包被跳过并计入 `Parser.unparsed`（坏包不中断整个文件）；
  3. 变长包（FT grid / FT yingtian / APP）按 `io.pos()` 推进，多包连续解析正确；
  4. 输出字段同时包含 seq 字段与 instances，且 ksy 的 `crc_*` 元数据实例不写进记录。
"""
import pytest

from _packets import (APP_ENTRY, CRC_SPECS, FIXED_IDS, FIXED_SPECS, FT_ENTRY,
                      FT_MAGIC, FT_TAIL, FT_YINGTIAN_ENTRY, build_app, build_fixed,
                      build_ft, build_ft_yingtian, entry_for, flip_byte)
from src.parser import Parser

MAGIC_SPECS = tuple(s for s in FIXED_SPECS if s.magic)
MAGIC_IDS = [s.key for s in MAGIC_SPECS]


# --------------------------------------------------------------------------- #
# 定长格式
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("spec", FIXED_SPECS, ids=FIXED_IDS)
def test_fixed_packet_parses(spec, packet_file):
    """一包合法数据：解析出 1 包、无 trailing、无 unparsed、帧长与 conf/ksy 一致。"""
    path = packet_file(build_fixed(spec), f"one{spec.ext}")
    parser = Parser(entry_for(spec), str(path))

    assert len(parser.packets) == 1
    assert parser.unparsed == 0
    assert parser.trailing == 0
    assert parser.packet_len == spec.plen
    assert len(parser.raw_chunks) == 1
    assert len(parser.raw_chunks[0]) == spec.plen
    assert parser.fields, "解析出的字段列表不应为空"


@pytest.mark.parametrize("spec", FIXED_SPECS, ids=FIXED_IDS)
def test_fixed_record_values(spec, packet_file):
    """帧头/帧尾按 `contents` 解析成十六进制串；`crc_*` 元数据实例不进输出。"""
    path = packet_file(build_fixed(spec), f"rec{spec.ext}")
    parser = Parser(entry_for(spec), str(path))
    record = parser.to_records()[0]

    assert set(record) == set(parser.fields)
    if spec.magic:
        assert record["header"] == spec.magic.hex()
    if spec.tail_at >= 0:
        assert record["tail"] == spec.tail.hex()
    if "body_data" in record:                 # ksy instances 的字节视图
        body = record["body_data"]             # u1 repeat -> list[int]；size: -> hex 串
        prefix = bytes(body) if isinstance(body, list) else bytes.fromhex(body)
        assert parser.raw_chunks[0].startswith(prefix)
    assert not [f for f in parser.fields if f.startswith("crc_")], \
        "ksy 的 CRC 元数据实例（crc_tail/…）不应写入输出记录"


@pytest.mark.parametrize("spec", MAGIC_SPECS, ids=MAGIC_IDS)
def test_wrong_magic_is_skipped_not_fatal(spec, packet_file):
    """帧头被破坏 -> 该包计入 unparsed；文件里没有可解析的包时抛 RuntimeError（附跳过数）。"""
    path = packet_file(flip_byte(build_fixed(spec), 0), f"bad{spec.ext}")

    with pytest.raises(RuntimeError, match="已跳过 1 个校验失败的包"):
        Parser(entry_for(spec), str(path))


def test_bad_packet_does_not_break_the_file(packet_file):
    """坏包 + 好包：只跳过坏包，好包照常解析（与“CRC 失败丢包”同一粒度）。"""
    spec = next(s for s in FIXED_SPECS if s.key == "grid1x_hk")
    good = build_fixed(spec)
    path = packet_file(flip_byte(good, 0) + good, "mixed.hk")

    parser = Parser(entry_for(spec), str(path))
    assert len(parser.packets) == 1
    assert parser.unparsed == 1
    assert parser.trailing == 0


def test_trailing_bytes_are_reported(packet_file):
    """不足一包的尾部字节计入 trailing，不参与解析。"""
    spec = next(s for s in FIXED_SPECS if s.key == "grid1x_hk")
    path = packet_file(build_fixed(spec) + b"\x01\x02\x03", "tail.hk")

    parser = Parser(entry_for(spec), str(path))
    assert len(parser.packets) == 1
    assert parser.trailing == 3


def test_multiple_fixed_packets(packet_file):
    """定长格式按 PACKET_LEN 顺序切片：3 包 -> 3 条记录。"""
    spec = next(s for s in FIXED_SPECS if s.key == "grid1x_es")
    path = packet_file(build_fixed(spec) * 3, "three.es")

    parser = Parser(entry_for(spec), str(path))
    assert len(parser.packets) == 3
    assert len(parser.to_records()) == 3
    assert parser.trailing == 0


# --------------------------------------------------------------------------- #
# 变长格式
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("n_events", [1, 2, 5])
def test_ft_grid_variable_length(n_events, packet_file):
    """grid 版 FT：44 + N*20；事件数由 pkg_event_num 决定，每事件含自己的 crc + 帧尾。"""
    path = packet_file(build_ft(n_events), "one.ft")
    parser = Parser(FT_ENTRY, str(path))

    assert parser.packet_len == 0
    assert len(parser.packets) == 1
    assert parser.trailing == 0

    packet = parser.packets[0]
    assert packet.header == FT_MAGIC
    assert packet.pkg_event_num == n_events
    assert len(packet.events) == n_events
    assert packet.events[-1].tail == FT_TAIL
    assert parser.to_records()[0]["header"] == FT_MAGIC.hex()


@pytest.mark.parametrize("n_events", [1, 2, 5])
def test_ft_yingtian_variable_length(n_events, packet_file):
    """yingtian 版 FT：46 + N*20；前 N-1 个事件循环 + 1 个 last_event，整包一个帧尾。"""
    path = packet_file(build_ft_yingtian(n_events), "one.ft")
    parser = Parser(FT_YINGTIAN_ENTRY, str(path))

    assert len(parser.packets) == 1
    assert parser.trailing == 0

    packet = parser.packets[0]
    assert packet.pkg_event_num == n_events
    assert len(packet.events) == n_events - 1
    assert packet.last_event is not None
    assert packet.tail == FT_TAIL


def test_ft_multiple_packets_in_one_file(packet_file):
    """变长包按实际消耗字节推进：一个文件里连续 3 个不同事件数的包。"""
    path = packet_file(build_ft(2) + build_ft(3) + build_ft(1), "many.ft")
    parser = Parser(FT_ENTRY, str(path))

    assert [p.pkg_event_num for p in parser.packets] == [2, 3, 1]
    assert parser.trailing == 0


def test_ft_partial_trailing_is_reported(packet_file):
    """变长包里出现残包：无法构成完整包 -> 停止解析并计入 trailing。"""
    path = packet_file(build_ft(2) + build_ft(3)[:30], "cut.ft")
    parser = Parser(FT_ENTRY, str(path))

    assert len(parser.packets) == 1
    assert parser.trailing == 30


@pytest.mark.parametrize("data_len", [0, 16, 64])
def test_app_variable_length(data_len, packet_file):
    """APP：18 + data_len + 6；data 字段按 size: data_len 读变长体。"""
    path = packet_file(build_app(data_len), "one.app")
    parser = Parser(APP_ENTRY, str(path))

    assert len(parser.packets) == 1
    assert parser.trailing == 0

    packet = parser.packets[0]
    assert packet.header == bytes.fromhex("47524944")
    assert packet.data_len == data_len
    assert len(packet.data) == data_len


# --------------------------------------------------------------------------- #
# Parser 的输入校验
# --------------------------------------------------------------------------- #
def test_missing_module_or_class_raises(tmp_path):
    """入口缺 MODULE/CLASS 时给出可操作的报错（提示先编译 + 补 conf）。"""
    src = tmp_path / "whatever.bin"
    src.write_bytes(b"\x00" * 16)

    with pytest.raises(RuntimeError, match="未配置 MODULE/CLASS"):
        Parser({"NAME": "broken"}, str(src))


def test_crc_meta_instances_are_not_in_fields(packet_file):
    """带 CRC 元数据的格式：元数据实例可在对象上读取，但不出现在 fields/记录里。"""
    spec = next(s for s in CRC_SPECS if s.key == "grid1x_wf")
    path = packet_file(build_fixed(spec), "meta.wf")
    parser = Parser(entry_for(spec), str(path))

    assert parser.packets[0].crc_tail == 6      # ksy instances 可读
    assert "crc_tail" not in parser.fields
