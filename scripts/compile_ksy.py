#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""一键编译 spec/ 目录下所有 .ksy 为 Python 解析器，输出到 generated/（按子目录镜像）。

用法：
    python scripts/compile_ksy.py

依赖：pip install kaitai-struct-compiler kaitaistruct
"""
import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC_DIR = os.path.join(ROOT, "spec")       # .ksy 定义
OUT_DIR = os.path.join(ROOT, "generated")   # 生成代码

COMPILER = shutil.which("kaitai-struct-compiler") or "kaitai-struct-compiler"


def ensure_package(pkg_dir):
    """确保目录可作为 Python 包导入（生成 __init__.py）。"""
    os.makedirs(pkg_dir, exist_ok=True)
    init = os.path.join(pkg_dir, "__init__.py")
    if not os.path.exists(init):
        with open(init, "w", encoding="utf-8") as f:
            f.write("# auto-generated package\n")


def main():
    if not shutil.which("kaitai-struct-compiler"):
        print("未找到 kaitai-struct-compiler，请先执行: pip install kaitai-struct-compiler")
        return 1

    ksy_files = sorted(glob.glob(os.path.join(SPEC_DIR, "**", "*.ksy"), recursive=True))
    if not ksy_files:
        print("未找到 .ksy 文件，请先检查 spec/ 目录。")
        return 1

    ensure_package(OUT_DIR)
    failed = 0
    for ksy in ksy_files:
        rel = os.path.relpath(ksy, SPEC_DIR)
        rel_sub = os.path.dirname(rel)  # 相对子目录（可能为空字符串）
        out_sub = os.path.join(OUT_DIR, rel_sub) if rel_sub else OUT_DIR
        ensure_package(out_sub)

        out_rel = os.path.splitext(rel)[0] + ".py"
        print(f"[编译] spec/{rel} -> generated/{out_rel} ...")
        # Windows 上编译器为 .bat 启动脚本，需经 cmd.exe 执行 (shell=True)；
        # Python 会通过 list2cmdline 自动对含空格路径加引号。
        rc = subprocess.call(
            [COMPILER, "-t", "python", "-d", out_sub, ksy],
            cwd=ROOT,
            shell=os.name == "nt",
        )
        if rc != 0:
            print(f"[失败] {rel}")
            failed += 1
        else:
            print(f"[完成] {rel}")

    if failed:
        print(f"编译完成，共 {failed} 个文件失败。")
        return 1
    print("全部编译完成，输出目录: generated/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
