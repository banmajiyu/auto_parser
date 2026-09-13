#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""一键编译 ksy/ 目录下所有 .ksy 为 Python 解析器，输出到 generated/（按子目录镜像）。

ksy/ 是**唯一真源**：
  ksy/grid1x/    GRID-1X 各包（hk 187B / hk 178B / ft 两版 / wf / es）
  ksy/grid11b/   GRID-11B 遥测（96B，HEAD/TAIL）
  ksy/grid10b/   GRID-10B 旧版（187B HK、88B tel，按《使用说明》V1.1）
  ksy/misc/      iv / vbr / lvds / app
  ksy/_drafts/   历史草稿，**不编译**（目录名以 _ 开头或文件名以 _draft 结尾都跳过）

用法：
    python scripts/compile_ksy.py                 # ksy/**/*.ksy -> generated/
    python scripts/compile_ksy.py --out <目录>    # 指定输出目录（默认 generated/）

依赖：pip install kaitai-struct-compiler kaitaistruct
"""
import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KSY_DIR = os.path.join(ROOT, "ksy")         # .ksy 定义（唯一真源）
OUT_DIR = os.path.join(ROOT, "generated")   # 生成代码

# 兼容 Windows 控制台 cp1252 及输出重定向场景，避免中文打印报 UnicodeEncodeError
# （与 main.py 保持一致）
for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if callable(_reconfigure):
        try:
            _reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

COMPILER = shutil.which("kaitai-struct-compiler") or "kaitai-struct-compiler"


def ensure_package(pkg_dir):
    """确保目录可作为 Python 包导入（生成 __init__.py）。"""
    os.makedirs(pkg_dir, exist_ok=True)
    init = os.path.join(pkg_dir, "__init__.py")
    if not os.path.exists(init):
        with open(init, "w", encoding="utf-8") as f:
            f.write("# auto-generated package\n")


def is_draft(path):
    """草稿不进编译：目录名以 _ 开头（如 _drafts/）或文件名以 _draft 结尾。"""
    rel = os.path.relpath(path, KSY_DIR)
    parts = rel.split(os.sep)
    stem = os.path.splitext(parts[-1])[0]
    return any(p.startswith("_") for p in parts[:-1]) or stem.endswith("_draft")


def main():
    if not shutil.which("kaitai-struct-compiler"):
        print("未找到 kaitai-struct-compiler，请先执行: pip install kaitai-struct-compiler")
        return 1

    out_dir = OUT_DIR
    if "--out" in sys.argv:
        out_dir = os.path.abspath(sys.argv[sys.argv.index("--out") + 1])

    ksy_files = sorted(p for p in glob.glob(os.path.join(KSY_DIR, "**", "*.ksy"), recursive=True)
                       if not is_draft(p))
    if not ksy_files:
        print("未找到 .ksy 文件，请先检查 ksy/ 目录。")
        return 1

    ensure_package(out_dir)
    failed = 0
    for ksy in ksy_files:
        rel = os.path.relpath(ksy, KSY_DIR)
        rel_sub = os.path.dirname(rel)  # 相对子目录（可能为空字符串）
        out_sub = os.path.join(out_dir, rel_sub) if rel_sub else out_dir
        ensure_package(out_sub)

        out_rel = os.path.splitext(rel)[0] + ".py"
        print(f"[编译] ksy/{rel} -> {out_rel} ...")
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
    print(f"全部编译完成，输出目录: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
