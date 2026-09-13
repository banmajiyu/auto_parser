# -*- coding: utf-8 -*-
"""一次性工具：把 frameseq 写法的 ksy 压平成"单包"写法（配合 pipeline 按 PACKET_LEN 切片）。

变换内容：
  1. 根 `seq: - id: frames / type: <T> / repeat: eos`  ← 删除
  2. `<T>` 类型内部的 `seq:` / `instances:` 整体上提到根（缩进 -2）
  3. `types:` 里删除 `<T>`（其余参数化类型保留）
  4. meta.id 改名；补 file-extension

用法: python script/_once/flatten_frameseq.py <文件> <新meta.id> [扩展名]
"""
import re
import sys
from pathlib import Path
import yaml

sys.stdout.reconfigure(encoding="utf-8")


def flatten(path: Path, new_id: str, ext: str | None = None) -> None:
    text = path.read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    root_seq = doc["seq"]
    if len(root_seq) != 1 or root_seq[0].get("repeat") != "eos":
        raise SystemExit(f"{path}: 根 seq 不是单个 frames/repeat:eos，跳过")
    tname = root_seq[0]["type"]
    assert tname in (doc.get("types") or {}), f"{path}: types 里没有 {tname}"

    lines = text.splitlines(keepends=True)

    def find_line(pred, start=0):
        for i in range(start, len(lines)):
            if pred(lines[i]):
                return i
        return None

    i_root_seq = find_line(lambda l: l.rstrip("\n") == "seq:")
    if i_root_seq is None:
        raise SystemExit(f"{path}: 找不到根 seq:")
    i_after_root_seq = find_line(lambda l: l[:1] not in (" ", "\n", "#") and l.strip(),
                                 i_root_seq + 1)
    if i_after_root_seq is None:
        i_after_root_seq = len(lines)

    i_types = find_line(lambda l: l.rstrip("\n") == "types:")
    if i_types is None:
        raise SystemExit(f"{path}: 找不到 types:")
    # types 下的条目：两空格缩进 + 以冒号结尾
    type_entries = [i for i in range(i_types + 1, len(lines))
                    if re.match(r"^  \w+:", lines[i])]
    if not type_entries:
        raise SystemExit(f"{path}: types 下没有条目")
    i_type = next((i for i in type_entries if lines[i].startswith(f"  {tname}:")), None)
    if i_type is None:
        raise SystemExit(f"{path}: types 下找不到 {tname}:")
    nxt = [i for i in type_entries if i > i_type]
    i_type_end = nxt[0] if nxt else len(lines)

    body = lines[i_type + 1:i_type_end]
    # 按块内 `seq:` 的实际缩进整体左移，使其落到根级；类型自带的 `seq:` 行丢弃（根级用我们插入的）
    i_seq_line = next(i for i, l in enumerate(body) if l.strip() == "seq:")
    indent = len(body[i_seq_line]) - len(body[i_seq_line].lstrip())
    body = [(l[indent:] if l.startswith(" " * indent) else l) for l in body]
    del body[i_seq_line]
    # 去掉 body 末尾多余空行
    while body and not body[-1].strip():
        body.pop()

    head = lines[:i_root_seq]                       # meta/doc/enums 等（到根 seq 之前）
    mid = lines[i_after_root_seq:i_type]            # 根 seq 之后、frame 类型之前（types: 头 + 其它类型）
    tail = lines[i_type_end:]                       # frame 之后的内容（正常为空）

    out = head + ["seq:\n"] + body + ["\n"] + mid + tail

    # meta.id / file-extension
    txt = "".join(out)
    txt = re.sub(r"(^meta:\n(?:.*\n)*?  id: )\S+", rf"\g<1>{new_id}", txt, count=1)
    if ext and "file-extension:" not in txt:
        txt = re.sub(r"(^meta:\n(?:.*\n)*?  endian: \w+\n)",
                     rf"\g<1>  file-extension: {ext}\n", txt, count=1)
    path.write_text(txt, encoding="utf-8")
    print(f"[flatten] {path} -> meta.id={new_id}, 忽略 types.{tname}, 根字段 {len(body)} 行")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    flatten(Path(sys.argv[1]), sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
