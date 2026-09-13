# -*- coding: utf-8 -*-
"""注册表（conf）/ 真源（ksy）/ 产物（generated）三者的一致性测试。

这些用例不解析数据，只保证“注册表、定义、生成代码、测试资产”不脱节：
新增了解析器却没写测试、改了 ksy 却忘了编译、发版忘了同步版本号，都会在这里失败。
"""
import importlib
import json
import re
from pathlib import Path

import pytest

from _packets import APP_ENTRY, FIXED_SPECS, FT_ENTRY, FT_YINGTIAN_ENTRY
from conftest import CONF_PATH, ENTRIES, ROOT
from src.validator import load_algorithms
from src.writer import Writer

# 变长格式的模块（PACKET_LEN=0，不在 FIXED_SPECS 里）
VARIABLE_MODULES = {FT_ENTRY["MODULE"], FT_YINGTIAN_ENTRY["MODULE"], APP_ENTRY["MODULE"]}
COVERED_MODULES = {spec.module for spec in FIXED_SPECS} | VARIABLE_MODULES

REQUIRED_KEYS = ("NAME", "TYPE", "MODULE", "CLASS", "PACKET_LEN", "DESCRIPTION", "VERSION")


def conf() -> dict:
    return json.loads(CONF_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# conf 注册表
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name", sorted(ENTRIES))
def test_conf_entry_has_required_keys(name):
    entry = ENTRIES[name]
    for key in REQUIRED_KEYS:
        assert key in entry, f"{name} 缺少 {key}"
    assert entry["TYPE"].startswith(".") and len(entry["TYPE"]) > 1
    assert isinstance(entry["PACKET_LEN"], int) and entry["PACKET_LEN"] >= 0


@pytest.mark.parametrize("name", sorted(ENTRIES))
def test_registered_module_and_class_are_importable(name):
    """每条注册项都能动态导入（MODULE 为 generated/ 下的包路径.模块名）。"""
    entry = ENTRIES[name]
    module = importlib.import_module(entry["MODULE"])
    assert hasattr(module, entry["CLASS"]), (
        f"{name}: {entry['MODULE']} 里没有 {entry['CLASS']}（ksy 改过？需重新编译）"
    )


def test_conf_packet_len_matches_layout_table():
    """conf 的 PACKET_LEN/TYPE 与测试布局表一致（两边都源于 ksy，改一处必须改另一处）。"""
    by_module = {entry["MODULE"]: entry for entry in ENTRIES.values()}
    for spec in FIXED_SPECS:
        entry = by_module.get(spec.module)
        if entry is None:
            continue
        assert entry["PACKET_LEN"] == spec.plen, f"{entry['NAME']} 的 PACKET_LEN 与布局表不符"
        assert entry["TYPE"] == spec.ext, f"{entry['NAME']} 的 TYPE 与布局表不符"


def test_variable_format_entries_use_zero_packet_len():
    """变长包约定：PACKET_LEN=0 表示按 io.pos() 逐包解析。"""
    for entry in (FT_ENTRY, FT_YINGTIAN_ENTRY, APP_ENTRY):
        assert ENTRIES[entry["NAME"]]["PACKET_LEN"] == 0


def test_conf_registers_every_layout_in_table():
    """反向：测试布局表里的格式应当都在 conf 注册（“注册所有解析器”的约定）。"""
    by_module = {entry["MODULE"]: entry["NAME"] for entry in ENTRIES.values()}
    unregistered = sorted(spec.module for spec in FIXED_SPECS if spec.module not in by_module)
    unregistered += sorted(m for m in VARIABLE_MODULES if m not in by_module)
    assert not unregistered, f"以下格式未注册进 conf.json：{unregistered}"


def test_every_registered_module_is_covered_by_tests():
    """反向检查：注册了解析器但没有测试资产 -> 失败（防止漏测）。"""
    uncovered = sorted(name for name, entry in ENTRIES.items()
                       if entry["MODULE"] not in COVERED_MODULES)
    assert not uncovered, f"以下解析器还没有测试布局（test/_packets.py）：{uncovered}"


def test_layout_table_entries_exist_in_generated():
    for spec in FIXED_SPECS:
        target = ROOT / "generated" / Path(*spec.module.split(".")).with_suffix(".py")
        assert target.exists(), f"缺少生成代码：{target.relative_to(ROOT)}（先运行 scripts/compile_ksy.py）"


# --------------------------------------------------------------------------- #
# ksy 真源 -> generated 产物
# --------------------------------------------------------------------------- #
def test_every_ksy_is_compiled():
    """ksy/ 下所有非草稿 .ksy 都应有生成模块（模块名 = meta.id，目录镜像）。"""
    yaml = pytest.importorskip("yaml")
    missing = []
    for ksy in sorted((ROOT / "ksy").rglob("*.ksy")):
        if "_drafts" in ksy.parts or ksy.stem.endswith("_draft"):
            continue
        meta_id = yaml.safe_load(ksy.read_text(encoding="utf-8"))["meta"]["id"]
        target = ROOT / "generated" / ksy.relative_to(ROOT / "ksy").parent / f"{meta_id}.py"
        if not target.exists():
            missing.append(str(target.relative_to(ROOT)))
    assert not missing, f"以下 ksy 尚未编译（运行 scripts/compile_ksy.py）：{missing}"


def test_ksy_meta_ids_are_unique():
    """meta.id 决定模块名，重复会导致 generated/ 里互相覆盖。"""
    yaml = pytest.importorskip("yaml")
    seen = {}
    for ksy in sorted((ROOT / "ksy").rglob("*.ksy")):
        if "_drafts" in ksy.parts or ksy.stem.endswith("_draft"):
            continue
        meta_id = yaml.safe_load(ksy.read_text(encoding="utf-8"))["meta"]["id"]
        seen.setdefault(meta_id, []).append(ksy.name)
    duplicated = {k: v for k, v in seen.items() if len(v) > 1}
    assert not duplicated, f"meta.id 重复：{duplicated}"


# --------------------------------------------------------------------------- #
# 顶层配置（OUTPUT_TYPE / CRC_ALGO / VERSION）
# --------------------------------------------------------------------------- #
def test_conf_output_type_is_supported():
    assert set(conf().get("OUTPUT_TYPE") or []) <= set(Writer.SUPPORTED)


def test_conf_crc_algo_table_is_loadable():
    table = load_algorithms(str(CONF_PATH))
    assert "crc16_ccitt" in table
    for name, algo in table.items():
        assert callable(algo["FUNC"]), f"{name} 的 FUNC 未能导入"
        assert algo["SIZE"] > 0 and algo["TAIL"] >= algo["SIZE"]


def test_conf_version_matches_changelog_head():
    """发版检查：conf.json 的 VERSION 与 CHANGELOG 顶部版本保持一致。"""
    version = conf()["VERSION"]
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(r"^##\s*v?([0-9][0-9.]*)", changelog, re.M)
    assert match, "CHANGELOG 里找不到 '## vX.Y' 形式的版本标题"
    assert match.group(1) == version, (
        f"CHANGELOG 顶部为 {match.group(1)}，conf.json 的 VERSION 为 {version}"
    )


def test_help_text_lists_capabilities_from_single_source():
    """`python main.py -h` 的清单取自 Writer.SUPPORTED 与 conf 的 CRC_ALGO（不重复声明能力）。"""
    from main import build_guidance

    text = build_guidance()
    for fmt in Writer.SUPPORTED:
        assert fmt in text
    for name in load_algorithms():
        assert name in text
