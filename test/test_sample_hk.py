# -*- coding: utf-8 -*-
"""真实样本 `test/sample.hk`（517 × 178B）的解析与校验测试。

该样本是仓库里**唯一**纳入版本管理的真实数据（`in/` 下其余样本都被 .gitignore 忽略），
它对应 yingtian 版 178B HK 布局（`ksy/grid1x/grid1x_hk_packet_178.ksy`），
与 conf 里另外两个 187B 版（grid1x / grid10b）**不是同一套标准** —— 见 `doc/工程手册.md` §11.5。
"""
from conftest import ENTRIES, ROOT

from src.parser import Parser
from src.validator import Validator

SAMPLE = ROOT / "test" / "sample.hk"

N_PACKETS = 517          # 517 × 178 = 92026
PACKET_LEN = 178

# 178B 版同样注册在 conf 里（与 187B 版同为 .hk，CLI 会列出菜单选择）
HK178 = ENTRIES["grid1x_hk_178_parser"]
HK187 = ENTRIES["grid1x_hk_parser"]


def test_sample_file_size_matches_517_packets():
    assert SAMPLE.exists(), "真实样本应随仓库提交（test/sample.hk）"
    assert SAMPLE.stat().st_size == N_PACKETS * PACKET_LEN


def test_hk178_parses_all_packets():
    parser = Parser(HK178, str(SAMPLE))

    assert len(parser.packets) == N_PACKETS
    assert parser.unparsed == 0
    assert parser.trailing == 0
    assert parser.packet_len == PACKET_LEN
    assert len(parser.raw_chunks) == N_PACKETS


def test_hk178_crc_passes_for_every_packet():
    """端到端：178B 布局 + CRC16（crc_tail=2, 覆盖 [0,176)）全部 517 包通过。"""
    parser = Parser(HK178, str(SAMPLE))
    validator = Validator(parser)

    records = validator.process()
    assert validator.checked == N_PACKETS
    assert validator.dropped == 0
    assert len(records) == N_PACKETS


def test_hk178_record_values_are_stable():
    """首包关键字段作为回归基线（改 ksy 布局会立刻在这里暴露）。"""
    parser = Parser(HK178, str(SAMPLE))
    records = Validator(parser).process()

    assert records[0]["utc_time"] == 1520598908
    # 带换算的字段输出为 {raw, converted}
    sipm_temp0 = records[0]["sipm_temp0"]
    assert sipm_temp0["raw"] == 26652
    assert sipm_temp0["converted"] == 26652 * 0.01 - 273.15
    # 时间戳单调不减，且首尾都在样本已知时间窗内
    times = [r["utc_time"] for r in records]
    assert times == sorted(times)
    assert times[0] == 1520598908 and 1520598908 < times[-1] < 1520599600


def test_hk187_parser_rejects_178_format():
    """版本不匹配：用 187B 解析器读 178B 数据 —— 大多数包被 contents 校验拦下、
    侥幸对齐的 3 个包被 CRC 全部丢弃，不会有错误数据流出。"""
    parser = Parser(HK187, str(SAMPLE))

    assert parser.packet_len == 187
    assert len(parser.packets) == 3
    assert parser.unparsed == 489                 # 92026 // 187 = 492 个切片
    assert parser.trailing == 22                  # 92026 % 187

    validator = Validator(parser)
    records = validator.process()
    assert validator.checked == 3 and validator.dropped == 3
    assert records == []
