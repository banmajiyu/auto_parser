# -*- coding: utf-8 -*-
"""流水线（Pipeline）与落盘（Writer）的测试。

Pipeline 把 Parser -> Validator -> Writer 串起来，是本工具对外的**主要 API**；
这里覆盖：结果字典的字段、坏包计数、`output_type=[]`（仅解析）、CSV/JSON/Parquet 三种产物、
以及 `main.run()` 这层薄 CLI 封装。
"""
import csv
import json
from pathlib import Path

import pytest

from _packets import FIXED_SPECS, build_fixed, entry_for, flip_byte
from conftest import ENTRIES
from src.pipeline import Pipeline
from src.writer import Writer

HK_SPEC = next(s for s in FIXED_SPECS if s.key == "grid1x_hk")
HK_ENTRY = ENTRIES["grid1x_hk_parser"]


# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #
def test_pipeline_result_contract(packet_file, tmp_path):
    """结果字典的键与取值：解析 1 包、CRC 通过、写出 1 条记录。"""
    src = packet_file(build_fixed(HK_SPEC), "one.hk")
    result = Pipeline(HK_ENTRY, str(src), str(tmp_path / "out"), output_type=["json"]).run()

    assert set(result) == {"packet_len", "count", "unparsed", "valid", "dropped",
                           "checked", "trailing", "paths"}
    assert result["packet_len"] == 187
    assert result["count"] == 1
    assert result["unparsed"] == 0
    assert result["valid"] == 1
    assert result["checked"] == 1
    assert result["dropped"] == 0
    assert result["trailing"] == 0
    assert Path(result["paths"]["json"]).exists()


def test_pipeline_default_output_type_writes_csv_and_json(packet_file, tmp_path):
    src = packet_file(build_fixed(HK_SPEC), "two.hk")
    result = Pipeline(HK_ENTRY, str(src), str(tmp_path / "out")).run()

    assert set(result["paths"]) == {"csv", "json"}
    assert all(Path(p).exists() for p in result["paths"].values())


def test_pipeline_empty_output_type_only_parses(packet_file, tmp_path):
    """output_type=[] 表示只解析不写文件（空列表不能被当成“用默认值”）。"""
    out = tmp_path / "out"
    src = packet_file(build_fixed(HK_SPEC), "only.hk")
    result = Pipeline(HK_ENTRY, str(src), str(out), output_type=[]).run()

    assert result["valid"] == 1
    assert result["paths"] == {}
    assert not out.exists()


def test_pipeline_counts_dropped_packets(packet_file, tmp_path):
    """坏 CRC 的包被计入 dropped/checked，且不产出文件。"""
    src = packet_file(flip_byte(build_fixed(HK_SPEC), HK_SPEC.crc_at), "bad.hk")
    result = Pipeline(HK_ENTRY, str(src), str(tmp_path / "out"), output_type=["json"]).run()

    assert result["count"] == 1 and result["checked"] == 1
    assert result["dropped"] == 1 and result["valid"] == 0
    assert result["paths"] == {}


def test_pipeline_variable_length_format(tmp_path):
    """变长包（FT，PACKET_LEN=0）也能走完整流水线。"""
    from _packets import build_ft

    src = tmp_path / "many.ft"
    src.write_bytes(build_ft(2) + build_ft(3))
    result = Pipeline(ENTRIES["grid1x_ft_parser"], str(src), str(tmp_path / "out"),
                      output_type=["json"]).run()

    assert result["packet_len"] == 0
    assert result["count"] == 2 and result["valid"] == 2
    assert result["checked"] == 2 and result["dropped"] == 0
    assert result["trailing"] == 0


def test_main_run_wrapper(packet_file, tmp_path):
    """main.run() 只是打印参数表 + 调 Pipeline，返回值应与 Pipeline 一致。"""
    from main import run

    src = packet_file(build_fixed(HK_SPEC), "cli.hk")
    result = run(HK_ENTRY, str(src), str(tmp_path / "out"), ".hk", ["json"])

    assert result["count"] == 1 and result["valid"] == 1
    assert Path(result["paths"]["json"]).exists()


# --------------------------------------------------------------------------- #
# Writer
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("fmt", list(Writer.SUPPORTED))
def test_writer_supports_each_format(fmt, tmp_path):
    if fmt == "parquet":
        pytest.importorskip("pyarrow")
    data = [{"a": 1, "b": {"raw": 2, "converted": 0.2}},
            {"a": 3, "b": {"raw": 4, "converted": 0.4}}]

    paths = Writer(data, str(tmp_path), "demo", type=[fmt]).write()
    assert Path(paths[fmt]).exists()
    assert Path(paths[fmt]).name == f"demo_packets.{fmt}"


def test_writer_csv_is_excel_friendly_and_flat(tmp_path):
    data = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    path = Path(Writer(data, str(tmp_path), "demo", type=["csv"]).write()["csv"])

    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf"), "CSV 应为 utf-8-sig（Excel 友好）"
    rows = list(csv.reader(path.read_text(encoding="utf-8-sig").splitlines()))
    assert rows == [["a", "b"], ["1", "x"], ["2", "y"]]


def test_writer_json_keeps_nested_structure(tmp_path):
    data = [{"a": 1, "b": {"raw": 2, "converted": 0.2}}]
    path = Path(Writer(data, str(tmp_path), "demo", type=["json"]).write()["json"])

    assert json.loads(path.read_text(encoding="utf-8")) == data


def test_writer_accepts_comma_separated_string(tmp_path):
    paths = Writer([{"a": 1}], str(tmp_path), "demo", type="json,csv").write()
    assert set(paths) == {"json", "csv"}


def test_writer_deduplicates_formats(tmp_path):
    paths = Writer([{"a": 1}], str(tmp_path), "demo", type=["json", "json"]).write()
    assert set(paths) == {"json"}


def test_writer_rejects_unknown_format(tmp_path):
    with pytest.raises(ValueError, match="不支持的输出格式"):
        Writer([{"a": 1}], str(tmp_path), "demo", type=["xml"])


def test_writer_rejects_empty_data(tmp_path):
    with pytest.raises(ValueError, match="无可写数据"):
        Writer([], str(tmp_path), "demo", type=["json"])


def test_writer_parquet_roundtrip(tmp_path):
    pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")

    data = [{"a": 1, "b": {"raw": 2, "converted": 0.2}}, {"a": 3, "b": {"raw": 4, "converted": 0.4}}]
    path = Path(Writer(data, str(tmp_path), "demo", type=["parquet"]).write()["parquet"])

    table = pq.read_table(path)
    assert table.num_rows == 2
    assert table.column("a").to_pylist() == [1, 3]
    assert table.schema.field("b").type.num_fields == 2      # 嵌套 struct 被保留


def test_writer_creates_destination_directory(tmp_path):
    des = tmp_path / "not" / "yet"
    paths = Writer([{"a": 1}], str(des), "demo", type=["json"]).write()
    assert Path(paths["json"]).parent == des


def test_entry_for_matches_registered_entry():
    """测试内置入口与 conf 注册信息一致（改 conf 后测试资产要同步）。"""
    spec = entry_for(HK_SPEC)
    assert spec["MODULE"] == HK_ENTRY["MODULE"]
    assert spec["CLASS"] == HK_ENTRY["CLASS"]
    assert spec["PACKET_LEN"] == HK_ENTRY["PACKET_LEN"]
