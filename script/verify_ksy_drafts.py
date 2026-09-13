# -*- coding: utf-8 -*-
"""ksy/ 体检：把每个 .ksy 的字段布局与对应参考 XML 按“字节边界”对撞。

参考 XML：
  grid     = xml/grid_packet.xml
  yingtian = grid_parser_ref/yingtian_packet.xml

输出每个文件的：帧长、帧头 magic、与参考 XML 的字段边界差异、前几处字段名差异。
用法: python script/verify_ksy_drafts.py
"""
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
import yaml

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]

XMLS = {
    "grid": ROOT / "xml" / "grid_packet.xml",
    "yingtian": ROOT / "grid_parser_ref" / "yingtian_packet.xml",
}

# (ksy 相对路径, 参考XML, 参考 tag)；tag=None 表示无参考
CHECKS = [
    ("grid1x/grid1x_hk_packet.ksy", "grid", "grid1x_hk_packet"),
    ("grid1x/grid1x_hk_packet_178.ksy", "yingtian", "hk_packet"),
    ("grid1x/grid1x_ft_packet.ksy", "grid", "grid1x_ft_packet"),
    ("grid1x/grid1x_ft_packet_yingtian.ksy", "yingtian", "grid1x_ft_packet"),
    ("grid1x/grid1x_wf_packet.ksy", "grid", "grid1x_wf_packet"),
    ("grid1x/grid1x_es_packet.ksy", "grid", "grid1x_es_packet"),
    ("grid11b/grid11b_telemetry_packet.ksy", "grid", "grid11b_telemetry_packet"),
    ("grid10b/grid10b_hk_packet.ksy", "grid", "grid1x_hk_packet"),
    ("grid10b/grid10b_tel_packet.ksy", None, None),
    ("misc/iv_packet.ksy", "grid", "iv_packet"),
    ("misc/vbr_packet.ksy", "grid", "vbr_packet"),
    ("misc/lvds_packet.ksy", "grid", "lvds_packet"),
    ("misc/app_packet.ksy", "grid", "app_packet"),
]

WIDTH = {"u1": 1, "u2": 2, "u4": 4, "u8": 8,
         "s1": 1, "s2": 2, "s4": 4, "s8": 8, "f4": 4, "f8": 8}


def xml_layout(kind, tag):
    """解析参考 XML，返回 (head, [(start, end, name), ...])"""
    pkt = ET.parse(XMLS[kind]).getroot().find(tag)
    head = bytes(int(v, 16) for v in pkt.attrib["head"].split(";"))
    base_wf = None
    for et in pkt.findall("./"):
        if et.tag == "waveform_data":
            base_wf = (int(et.find("start").text), int(et.find("size").text),
                       int(et.find("len").text))
    fields = []
    for et in pkt.findall("./"):
        st = et.find("start")
        s = int(st.text)
        if "vary_wf" in st.attrib and base_wf:
            s += base_wf[0] + base_wf[1] * base_wf[2]
        if any(k in st.attrib for k in ("vary_repeat", "vary_tag")):
            continue                                   # 变长/模板字段不参与静态对撞
        size = int(et.find("size").text)
        ln = int(et.find("len").text)
        fields.append((s, s + size * ln, et.tag))
    return head, fields


def ksy_layout(doc):
    """切分ksy各层次"""
    seq = doc.get("seq") or []
    types = doc.get("types") or {}
    out = []
    _walk(seq, types, 0, out, "")
    return out


def _walk(seq, types, off, out, prefix):
    """递归展开 seq，按字节边界输出 [(start, end, name), ...]；off=None 表示未知偏移。"""
    for e in seq:
        name = prefix + e["id"]
        t = e.get("type")
        rep = e.get("repeat-expr")
        cnt = rep if isinstance(rep, int) else (1 if rep is None else None)
        if off is None:
            out.append((None, None, name))
            continue
        if "size" in e:
            n = e["size"] if isinstance(e["size"], int) else None
            if n is None:
                out.append((off, None, name))
                off = None
                continue
            out.append((off, off + n * (cnt or 0), name))
            off += n * (cnt or 0)
            continue
        if "contents" in e:
            n = len(e["contents"])
            out.append((off, off + n, name))
            off += n
            continue
        if t in WIDTH:
            w = WIDTH[t] * (cnt or 1)
            out.append((off, off + w, name))
            if cnt is None:
                out.append((off, None, name + "[]"))
                off = None
                continue
            off += w
            continue
        if isinstance(t, str) and "(" in t:
            t = t.split("(")[0]
        if t in types:
            inner = []
            _walk(types[t].get("seq") or [], types, off, inner, prefix=name + ".")
            out.extend(inner)
            if cnt is None:
                out.append((off, None, name + "[]"))
                off = None
                continue
            end = max((v[1] for v in inner if v[1] is not None), default=None)
            if end is None:
                out.append((off, None, name))
                off = None
                continue
            item = end - off
            out.append((off, off + item * cnt, name))
            off += item * cnt
            continue
        out.append((off, None, f"{name}(?)"))
        off = None


def seg(a, b):
    """ 对撞两个字段布局，返回差异段列表 [(lo, hi, name_a, name_b), ...]
    - lo/hi: 字节边界
    - name_a: a 中该段对应的字段名（或 "—" 表示 a 没有该段）
    - name_b: b 中该段对应的字段名（或 "—" 表示 b 没有该段）"""
    bounds = sorted({0} | {x for f in (a, b) for p in f for x in p[:2] if x is not None})
    res = []
    for lo, hi in zip(bounds, bounds[1:]):
        na = next((n for s, e, n in a if s is not None and e is not None and s <= lo and hi <= e), "—")
        nb = next((n for s, e, n in b if s is not None and e is not None and s <= lo and hi <= e), "—")
        if na != nb:
            res.append((lo, hi, na, nb))
    return res


def main():
    print("=" * 100)
    print("A. 全部 ksy 的帧长 / magic（含 _drafts 之外的 ksy 树）")
    print("=" * 100)
    rows = []
    for rel, kind, tag in CHECKS:
        p = ROOT / "ksy" / rel
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        lay = ksy_layout(doc)
        ends = [v[1] for v in lay if v[1] is not None]
        end = max(ends) if ends else None
        mg = None
        for v in lay[:3]:
            for e in (doc.get("seq") or [])[:3]:
                if "contents" in e:
                    mg = bytes(e["contents"])
                    break
            break
        rows.append((rel, doc, lay, end, mg))
        print(f"  {rel:<46} meta.id={doc['meta'].get('id'):<28} 帧长={end} "
              f"magic={mg.hex(' ') if mg else '—'}")

    print()
    print("=" * 100)
    print("B. 与参考 XML 的字节边界对撞")
    print("=" * 100)
    for rel, doc, lay, end, mg in rows:
        kind = tag = None
        for r, k, t in CHECKS:
            if r == rel:
                kind, tag = k, t
        print("-" * 100)
        print(f"  ksy/{rel}  (帧长={end})")
        if not tag:
            print("    （无对应参考 XML，跳过）")
            continue
        head, xf = xml_layout(kind, tag)
        plen = int(ET.parse(XMLS[kind]).getroot().find(tag).attrib.get("packet_len", 0))
        xb = sorted({x for s, e, _ in xf for x in (s, e)})
        kb = sorted({x for s, e, _ in lay for x in (s, e) if x is not None})
        print(f"    参考 <{tag}> ({kind}, packet_len={plen}) vs ksy 帧长={end}"
              f"   magic {'一致' if mg == head else f'ksy={mg.hex() if mg else None} xml={head.hex()}'}")
        if xb == kb:
            print("    ✓ 字段边界完全一致")
        else:
            print(f"    ⚠ 仅 XML 有的边界: {[b for b in xb if b not in kb][:16]}")
            print(f"    ⚠ 仅 ksy 有的边界: {[b for b in kb if b not in xb][:16]}")
        d = seg(xf, lay)
        print(f"    字段名差异 {len(d)} 处，前 6 处：")
        for lo, hi, na, nb in d[:6]:
            print(f"      [{lo:>4},{hi:>4})  XML={na:<30} ksy={nb}")


if __name__ == "__main__":
    main()
