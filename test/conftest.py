# -*- coding: utf-8 -*-
"""pytest 全局配置：导入路径、工作目录、conf 注册表与临时文件夹具。

运行方式（必须在项目根目录执行，见下）：
    python -m pytest test -q
    python -m pytest test -q -k hk        # 只跑 HK 相关用例
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# 被测代码的导入路径：项目根（src 包）+ generated/（Kaitai 生成代码，.gitignore 忽略、需先编译）
for _path in (str(ROOT), str(ROOT / "generated")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

CONF_PATH = ROOT / "conf" / "conf.json"


def load_entries() -> dict:
    """conf.json 的 PARSER 注册表：{NAME: entry}。"""
    conf = json.loads(CONF_PATH.read_text(encoding="utf-8"))
    return {entry["NAME"]: entry for entry in conf["PARSER"]}


def load_conf() -> dict:
    """conf.json 的完整内容（顶层 OUTPUT_TYPE / CRC_ALGO / PARSER）。"""
    return json.loads(CONF_PATH.read_text(encoding="utf-8"))


ENTRIES = load_entries()


@pytest.fixture(autouse=True, scope="session")
def _run_at_project_root():
    """把工作目录切到项目根。

    `src/parser.py`、`src/validator.py` 里的 conf / generated 路径都是相对路径
    （`conf\\conf.json`、`generated`），`main.py` 也要求从项目根运行；统一在项目根下执行测试，
    避免“找得到 src、找不到 conf”的假失败。
    """
    old = os.getcwd()
    os.chdir(ROOT)
    try:
        yield
    finally:
        os.chdir(old)


@pytest.fixture
def packet_file(tmp_path):
    """把内存中合成的字节写到一个临时文件，返回该文件路径。"""
    def _write(data: bytes, name: str = "sample.bin") -> Path:
        path = tmp_path / name
        path.write_bytes(data)
        return path
    return _write
