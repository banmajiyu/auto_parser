# -*- coding: utf-8 -*-
"""CRC 校验测试：算法标准值、conf 策略解析、包级校验与丢弃行为。

对应文档：`doc/工程手册.md` §7（CRC16 校验）与 `doc/crc_reference.md`。
"""
import zlib

import pytest

from _packets import (CRC_SPECS, FT_ENTRY, FT_YINGTIAN_ENTRY, NO_CRC_SPECS,
                      build_fixed, build_ft, build_ft_yingtian, entry_for, flip_byte)
from src.checks.crc16_ccitt import crc16_ccitt
from src.checks.crc32 import crc32
from src.parser import Parser
from src.validator import Validator, get_algorithm, list_algorithms, resolve_policy

CRC_IDS = [s.key for s in CRC_SPECS]
NO_CRC_IDS = [s.key for s in NO_CRC_SPECS]


# --------------------------------------------------------------------------- #
# 算法本身（标准校验值）
# --------------------------------------------------------------------------- #
def test_crc16_ccitt_standard_vector():
    """CRC-16/XMODEM（poly 0x1021, init 0x0000）："123456789" -> 0x31C3。"""
    assert crc16_ccitt(b"123456789") == 0x31C3
    assert crc16_ccitt(b"123456789", init=0xFFFF) == 0x29B1      # CCITT-FALSE


def test_crc32c_standard_vector_and_not_zlib():
    """CRC-32C（poly 0x1EDC6F41, init/xorout 0xFFFFFFFF）—— 不是 zlib 的 CRC-32。"""
    assert crc32(b"123456789") == 0xE3069283
    assert crc32(b"123456789") != zlib.crc32(b"123456789")       # 0xCBF43926


def test_init_zero_makes_all_zero_data_usr_crc_zero():
    """回归用：init=0 时全 0 数据的 CRC 恒为 0 —— 造测试数据不能用全 0。"""
    assert crc16_ccitt(bytes(64), init=0) == 0


# --------------------------------------------------------------------------- #
# conf 顶层的算法表与 SUPPORT 匹配
# --------------------------------------------------------------------------- #
def test_algorithms_are_registered_in_conf():
    assert set(list_algorithms()) >= {"crc16_ccitt", "crc32"}


def test_get_algorithm_returns_callable():
    algo = get_algorithm("crc16_ccitt")
    assert callable(algo["FUNC"]) and algo["FUNC"] is crc16_ccitt
    assert algo["SIZE"] == 2 and algo["INIT"] == 0x0000


def test_get_algorithm_unknown_name_lists_available():
    with pytest.raises(KeyError, match="未找到算法"):
        get_algorithm("no_such_algo")


@pytest.mark.parametrize("fmt,name,tail", [
    (".hk", "crc16_ccitt", 2),
    (".ft", "crc16_ccitt", 6),
    (".wf", "crc16_ccitt", 6),
    (".es", "crc16_ccitt", 6),
    (".iv", "crc32", 4),
    (".vbr", "crc32", 4),
])
def test_resolve_policy_matches_support(fmt, name, tail):
    """未显式指定算法时，按源文件后缀在 SUPPORT 里匹配（含按格式覆盖的 TAIL）。"""
    policy = resolve_policy(fmt)
    assert policy["NAME"] == name
    assert policy["TAIL"] == tail
    assert callable(policy["FUNC"])


@pytest.mark.parametrize("fmt", [".app", ".lvds", ".tlm", ".unknown"])
def test_resolve_policy_no_support_returns_none(fmt):
    """格式不在任何 SUPPORT 里 -> 不做校验（checked 不增加）。"""
    assert resolve_policy(fmt) is None


def test_resolve_policy_explicit_algo_overrides_support():
    policy = resolve_policy(".ft", "crc32")
    assert policy["NAME"] == "crc32" and policy["TAIL"] == 4


def test_resolve_policy_unknown_algo_raises():
    with pytest.raises(KeyError, match="未找到算法"):
        resolve_policy(".hk", "no_such_algo")


# --------------------------------------------------------------------------- #
# 包级校验：通过 / 丢弃 / 保留
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("spec", CRC_SPECS, ids=CRC_IDS)
def test_valid_crc_passes(spec, packet_file):
    path = packet_file(build_fixed(spec), f"ok{spec.ext}")
    parser = Parser(entry_for(spec), str(path))
    validator = Validator(parser)

    records = validator.process()
    assert validator.checked == 1
    assert validator.dropped == 0
    assert len(records) == 1


@pytest.mark.parametrize("spec", CRC_SPECS, ids=CRC_IDS)
def test_corrupted_crc_is_dropped(spec, packet_file):
    path = packet_file(flip_byte(build_fixed(spec), spec.crc_at), f"bad{spec.ext}")
    parser = Parser(entry_for(spec), str(path))
    validator = Validator(parser)

    records = validator.process()
    assert validator.checked == 1
    assert validator.dropped == 1
    assert records == []


@pytest.mark.parametrize("spec", CRC_SPECS, ids=CRC_IDS)
def test_drop_on_fail_false_keeps_bad_packet(spec, packet_file):
    """DROP_ON_FAIL=false：坏包保留、照常写出，`dropped` 只在真正丢弃时才计数（此时为 0）。"""
    path = packet_file(flip_byte(build_fixed(spec), spec.crc_at), f"keep{spec.ext}")
    parser = Parser(entry_for(spec), str(path))
    validator = Validator(parser, drop_on_fail=False)

    records = validator.process()
    assert validator.checked == 1
    assert validator.dropped == 0
    assert len(records) == 1


@pytest.mark.parametrize("spec", NO_CRC_SPECS, ids=NO_CRC_IDS)
def test_formats_without_crc_field_are_not_checked(spec, packet_file):
    """ksy 没有 crc 字段（如 iv/vbr/tlm/tel/lvds）-> 跳过校验，不影响解析。"""
    path = packet_file(build_fixed(spec), f"n{spec.ext}")
    parser = Parser(entry_for(spec), str(path))
    validator = Validator(parser)

    records = validator.process()
    assert validator.checked == 0
    assert validator.dropped == 0
    assert len(records) == 1


def test_crc_false_switch_skips_everything(packet_file):
    """总开关 crc=False -> 完全不校验（坏 CRC 也保留）。"""
    spec = next(s for s in CRC_SPECS if s.key == "grid1x_hk")
    path = packet_file(flip_byte(build_fixed(spec), spec.crc_at), "off.hk")
    parser = Parser(entry_for(spec), str(path))
    validator = Validator(parser, crc=False)

    assert len(validator.process()) == 1
    assert validator.checked == 0 and validator.dropped == 0


def test_partial_drop_keeps_good_packets(packet_file):
    """一个文件里好包/坏包混合：只丢坏包，好包照常输出。"""
    spec = next(s for s in CRC_SPECS if s.key == "grid1x_es")
    good = build_fixed(spec)
    path = packet_file(good + flip_byte(good, spec.crc_at) + good, "mix.es")
    parser = Parser(entry_for(spec), str(path))
    validator = Validator(parser)

    assert len(validator.process()) == 2
    assert validator.checked == 3 and validator.dropped == 1


def test_ksy_metadata_overrides_explicit_argument(packet_file):
    """优先级：ksy `instances` 的 crc_tail 优先于构造参数（WF 声明 6，传 2 也应通过）。"""
    spec = next(s for s in CRC_SPECS if s.key == "grid1x_wf")
    path = packet_file(build_fixed(spec), "wf.wf")
    parser = Parser(entry_for(spec), str(path))
    validator = Validator(parser, crc_tail=2)      # 故意传错，应被 ksy 元数据覆盖

    validator.process()
    assert validator.checked == 1 and validator.dropped == 0


def test_explicit_algo_overrides_ksy_declaration(packet_file):
    """显式指定的算法优先于 ksy 的 crc_algo：给 HK 指定 crc32 -> 必然校验不过。"""
    spec = next(s for s in CRC_SPECS if s.key == "grid1x_hk")
    path = packet_file(build_fixed(spec), "algo.hk")
    parser = Parser(entry_for(spec), str(path))
    validator = Validator(parser, crc_algo="crc32")

    validator.process()
    assert validator.checked == 1 and validator.dropped == 1


# --------------------------------------------------------------------------- #
# 变长格式（FT）的 CRC：只取最后一个事件的 crc，覆盖 [0, 包长-crc_tail)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("n_events", [1, 3])
def test_ft_grid_crc(n_events, packet_file):
    path = packet_file(build_ft(n_events), "ft.ft")
    parser = Parser(FT_ENTRY, str(path))
    validator = Validator(parser)

    validator.process()
    assert validator.checked == 1 and validator.dropped == 0


@pytest.mark.parametrize("n_events", [1, 3])
def test_ft_yingtian_crc(n_events, packet_file):
    path = packet_file(build_ft_yingtian(n_events), "yt.ft")
    parser = Parser(FT_YINGTIAN_ENTRY, str(path))
    validator = Validator(parser)

    validator.process()
    assert validator.checked == 1 and validator.dropped == 0


def test_ft_corrupted_last_event_crc_is_dropped(packet_file):
    data = build_ft(3)
    path = packet_file(flip_byte(data, len(data) - 6), "bad.ft")
    parser = Parser(FT_ENTRY, str(path))
    validator = Validator(parser)

    assert validator.process() == []
    assert validator.checked == 1 and validator.dropped == 1
