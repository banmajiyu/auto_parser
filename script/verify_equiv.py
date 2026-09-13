# -*- coding: utf-8 -*-
"""等价性实测：旧 grid_parser_ref 解析函数 vs 新 Parser/Validator。

  A) 定长包逐字段对照：按旧 XML 造包（帧头/帧尾写 XML 位置，其余字节 = (i*7+3)&0xFF），
     旧 parse_grid_data_single 与新 Parser 各解析一遍，比较同名字段值。
  A2) FT：20 字节/事件、事件数 = pkg_event_num，对比旧 vary_repeat 定位公式。
  B) 真实样本：in/sample.ft、in/sample.app（本地合成样本，未纳入版本管理）、
     test/sample.hk（真实数据，已提交）。
  C) 语义校验（CRC）：按旧规则位置/覆盖区间写入 CRC，比较旧 crc_check 与新 Validator。

用法: python script/verify_equiv.py
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import types
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

# ---- 旧代码 import crcmod（本机未装）→ 用本仓库 CRC-16/XMODEM 顶上 ----
if "crcmod" not in sys.modules:
    from src.checks.crc16_ccitt import crc16_ccitt as _crc16

    def _mkCrcFun(poly, rev=False, initCrc=0, xorOut=0):
        return lambda data: _crc16(bytes(data), init=initCrc) ^ xorOut

    _m = types.ModuleType("crcmod")
    _m.mkCrcFun = _mkCrcFun
    sys.modules["crcmod"] = _m

from grid_parser_ref.parse_grid_data import parse_grid_data_single          # noqa: E402
from src.parser import Parser                                               # noqa: E402
from src.validator import Validator, crc16_ccitt                            # noqa: E402

XML = ROOT / "xml" / "grid_packet.xml"
XML_ROOT = ET.parse(XML).getroot()
CONF = json.loads((ROOT / "conf" / "conf.json").read_text(encoding="utf-8"))
ENTRY = {e["NAME"]: e for e in CONF["PARSER"]}

N_PKT = 2          # 旧代码个别地方要 packet_num>1（squeeze 后取 [0]），统一造 2 个包
FT_TAIL = bytes.fromhex("cc118822")


def pattern(plen):
    return bytearray(((i * 7 + 3) & 0xFF) for i in range(plen))


def fields_of(tag):
    """字段 -> (start, size, len, start属性)；vary_wf 的 start 就地展开（基址 = waveform_data 之后）。"""
    pkt = XML_ROOT.find(tag)
    base_wf = None
    for et in pkt.findall("./"):
        if et.tag == "waveform_data":
            base_wf = (int(et.find("start").text), int(et.find("size").text),
                       int(et.find("len").text))
    out = {}
    for et in pkt.findall("./"):
        st = et.find("start")
        s = int(st.text)
        if base_wf and "vary_wf" in st.attrib:
            s += base_wf[0] + base_wf[1] * base_wf[2]
        out[et.tag] = (s, int(et.find("size").text), int(et.find("len").text),
                       dict(st.attrib))
    return out


def build(tag, plen, n_evt=0, step=0, n_pkt=N_PKT):
    """按旧 XML 的字段表造合成包（多包拼接）。WF/FT 需特殊布置。"""
    attrs, f = dict(XML_ROOT.find(tag).attrib), fields_of(tag)
    head = bytes(int(v, 16) for v in attrs["head"].split(";"))
    tail = bytes(int(v, 16) for v in attrs["tail"].split(";")) if "tail" in attrs else b""
    chunks = []
    for _ in range(n_pkt):
        b = pattern(plen)
        b[0:len(head)] = head
        if tag == "grid1x_wf_packet":
            st = f["sample_length"][0]                 # 旧代码用 sample_length 决定波形长度
            b[st:st + 2] = (256).to_bytes(2, "big")
            off = f["tail"][0]
            b[off:off + 4] = tail
        elif tag == "grid1x_ft_packet":
            b = build_ft(b, head, n_evt)
        elif tail:
            off = f["tail"][0]
            b[off:off + len(tail)] = tail
        chunks.append(bytes(b))
    return attrs, f, b"".join(chunks)


def build_ft(b, head, n_evt, step=20):
    """FT：固定头 44B + n_evt 个事件（14B 数据 + crc + tail）。"""
    b[34:36] = n_evt.to_bytes(2, "big")                 # pkg_event_num
    for i in range(n_evt):
        base = 44 + i * step
        for k, (off, size) in enumerate(((0, 4), (4, 2), (6, 2), (8, 4), (12, 2))):
            b[base + off:base + off + size] = (10 * (i + 1) + k).to_bytes(size, "big")
        crc_at = base + 14
        b[crc_at:crc_at + 2] = crc16_ccitt(bytes(b[:crc_at])).to_bytes(2, "big")
        b[base + 16:base + 20] = FT_TAIL
    return b


def old_parse(buf, tag, plen, n_evt=None, step=None, crc_check=False, endian="MSB",
              n_pkt=N_PKT):
    idx = np.array([[i * plen, (i + 1) * plen] for i in range(n_pkt)])
    kw = {"multi_evt": n_evt, "multi_step": step} if n_evt is not None else {}
    with contextlib.redirect_stdout(io.StringIO()):
        data, _ = parse_grid_data_single(
            "synthetic", idx, xml_file=str(XML), data_tag=tag, endian=endian,
            crc_check=crc_check, bcc_check=False,
            data_array=np.frombuffer(buf, np.uint8), packet_len=plen, **kw)
    return data


def new_parse(buf, entry, ext):
    dd = tempfile.mkdtemp()
    p = Path(dd) / f"x{ext}"
    p.write_bytes(buf)
    return Parser(ENTRY[entry], str(p))


def simp(v):
    """归一化：bytes -> int、scaled dict -> raw、十六进制串 -> int（
    迁移后 magic 字段改为 contents(bytes)、单位换算字段变为 {raw, converted}）。"""
    if isinstance(v, dict) and "raw" in v:
        return simp(v["raw"])
    if isinstance(v, bytes):
        return int.from_bytes(v, "big") if len(v) <= 8 else v.hex()
    if isinstance(v, str) and len(v) in (6, 8, 16) \
            and all(c in "0123456789abcdef" for c in v.lower()):
        return int(v, 16)
    return v


def compare(tag, ext, entry, plen, title=""):
    attrs, fields, buf = build(tag, plen)
    print("=" * 88)
    print(f"[{ext}] {tag} {title} packet_len={plen} ×{N_PKT} 合成包")
    try:
        old = old_parse(buf, tag, plen)
    except Exception as e:
        print(f"  旧解析异常: {type(e).__name__}: {e}")
        return
    parser = new_parse(buf, entry, ext)
    rec = parser.to_records()[0]
    diffs = []
    for fname, (s, size, length, sattr) in fields.items():
        key = fname.lower()
        if key not in rec:
            diffs.append((fname, f"XML@{s}", "ksy 无此字段（多为重命名）"))
            continue
        ov = old.get(fname)
        if ov is None:
            continue
        ov = np.asarray(ov).ravel()
        per = ov.size // N_PKT                 # 旧代码把每包结果顺序摊平
        ov = [simp(v) for v in ov[:per]]
        nv = rec[key]
        nv = [simp(v) for v in (nv if isinstance(nv, list) else [nv])]
        if len(ov) == len(nv) and all(a == b for a, b in zip(ov, nv)):
            continue
        diffs.append((fname, f"XML@{s}", f"old={ov[:4]} new={nv[:4]}"))
    if not diffs:
        print("  ✓ 旧/新同名字段值全部一致")
    else:
        for fname, where, detail in diffs:
            print(f"  ✗ {fname:<26}{where:<12}{detail}")


def crc_case(tag, ext, entry, plen, cover_end, store_at, title):
    attrs, fields, buf = build(tag, plen)
    b = bytearray(buf)
    crc = crc16_ccitt(bytes(b[:cover_end]))
    for i in range(N_PKT):
        b[i * plen + store_at:i * plen + store_at + 2] = crc.to_bytes(2, "big")
    buf = bytes(b)
    print("-" * 88)
    print(f"[{ext}] {title}")
    print(f"  写入: CRC16(raw[0:{cover_end}]) = 0x{crc:04X} -> 偏移 [{store_at},{store_at + 2})")
    try:
        old = old_parse(buf, tag, plen, crc_check=True)
        oc = np.asarray(old["crc_check"]).ravel()
        print(f"  旧 crc_check = {oc.tolist()}")
    except Exception as e:
        print(f"  旧 crc_check 异常: {type(e).__name__}: {e}")
    p = new_parse(buf, entry, ext)
    v = Validator(p)
    v.process()
    print(f"  新 Validator: checked={v.checked} dropped={v.dropped} "
          f"crc_tail={v.crc_tail} -> crc 起点 {plen - v.crc_tail}, 覆盖 [0,{plen - v.crc_tail})")


def wf_frame_find(title, tail_at):
    """旧代码的定帧方式：head + .{560} + tail（要求帧尾在包尾最后 4 字节）。"""
    import re
    _, f, buf = build("grid1x_wf_packet", 568)
    b = bytearray(pattern(568))
    b[0:4] = bytes.fromhex("2e2e33ff")
    b[tail_at:tail_at + 4] = bytes.fromhex("22eeff33")
    data = bytes(b) * 2
    pat = re.escape(b"\x2e\x2e\x33\xff") + b".{560}" + re.escape(b"\x22\xee\xff\x33")
    n = len(list(re.finditer(pat, data, re.S)))
    print(f"  帧尾写在偏移 {tail_at}（{title}）-> 旧定帧正则命中 {n} 个包")


def main():
    print("### A. 定长包逐字段对照（合成数据，逐字段比较旧/新）")
    for ext, tag, entry, plen in (
            (".hk", "grid1x_hk_packet", "grid1x_hk_parser", 187),
            (".wf", "grid1x_wf_packet", "grid1x_wf_parser", 568),
            (".es", "grid1x_es_packet", "grid1x_es_parser", 528),
            (".tlm", "grid11b_telemetry_packet", "grid11b_telemetry_parser", 96),
            (".iv", "iv_packet", "iv_parser", 412),
            (".vbr", "vbr_packet", "vbr_parser", 412),
            (".lvds", "lvds_packet", "lvds_parser", 2048)):
        compare(tag, ext, entry, plen)

    print("\n### A2. FT：20B/事件，事件数 = pkg_event_num")
    n, step = 3, 20
    plen = 44 + n * step
    attrs, fields, buf = build("grid1x_ft_packet", plen, n, step)
    p = new_parse(buf, "grid1x_ft_parser", ".ft")
    pk = p.packets[0]
    print(f"[.ft] 合成 packet_len={plen}，新解析 events={len(pk.events)} "
          f"crc={[hex(e.crc) for e in pk.events]} "
          f"tail={[getattr(e.tail, 'hex', lambda: e.tail)() for e in pk.events]}")
    for ne, st in ((n, 20), (n, 12), (40, 12)):
        try:
            old = old_parse(buf, "grid1x_ft_packet", plen, ne, st)
            print(f"  旧 multi_evt={ne:<3} multi_step={st:<3} -> "
                  f"timestamp={np.asarray(old['timestamp']).ravel().tolist()} "
                  f"CRC={np.asarray(old['CRC']).ravel().tolist()} "
                  f"tail={[hex(int(v)) for v in np.asarray(old['tail']).ravel()]}")
        except Exception as e:
            print(f"  旧 multi_evt={ne:<3} multi_step={st:<3} -> {type(e).__name__}: {e}")

    print("\n### B. 真实样本")
    ft = ROOT / "in" / "sample.ft"
    p = Parser(ENTRY["grid1x_ft_parser"], str(ft))
    pk = p.packets[0]
    print(f"[sample.ft] len={ft.stat().st_size} packets={len(p.packets)} trailing={p.trailing} "
          f"pkg_event_num={pk.pkg_event_num} events={len(pk.events)} "
          f"crc={[hex(e.crc) for e in pk.events]} "
          f"tail={[getattr(e.tail, 'hex', lambda: e.tail)() for e in pk.events]}")
    print("  旧的 vary_repeat 规则（N=事件数, step）会把 CRC 定到 base_start+N*step+2，"
          "而真实包长 = 44+N*20 → CRC 起点应 = 38+N*20")
    app = ROOT / "in" / "sample.app"
    pa = Parser(ENTRY["app_parser"], str(app))
    print(f"[sample.app] len={app.stat().st_size} packets={len(pa.packets)} trailing={pa.trailing} "
          f"data_len={pa.packets[0].data_len} check_sum={hex(pa.packets[0].check_sum)} "
          f"tail={hex(pa.packets[0].tail)}")
    hk = ROOT / "test" / "sample.hk"
    ph = Parser(ENTRY["grid1x_hk_parser"], str(hk))
    print(f"[sample.hk] len={hk.stat().st_size}（=517×178）按 187 切: packets={len(ph.packets)} "
          f"unparsed={ph.unparsed} trailing={ph.trailing}  ← 旧逻辑会用帧头正则找 517 个 187B 窗口")

    print("\n### C. 语义校验（CRC）旧 vs 新")
    crc_case("grid1x_hk_packet", ".hk", "grid1x_hk_parser", 187, 185, 185,
             "HK：XML CRC@185，覆盖 [0,185)")
    crc_case("grid1x_es_packet", ".es", "grid1x_es_parser", 528, 522, 522,
             "ES：XML CRC@522，覆盖 [0,522)")
    crc_case("grid1x_wf_packet", ".wf", "grid1x_wf_parser", 568, 562, 562,
             "WF：XML CRC@562，覆盖 [0,562)")
    crc_case("grid1x_wf_packet", ".wf", "grid1x_wf_parser", 568, 560, 560,
             "WF：ksy 布局 CRC@560，覆盖 [0,560)")

    print("\n### D. 其余语义差异")
    print("D1) WF 帧尾位置：")
    wf_frame_find("XML 规则：帧尾 = 包尾最后 4 字节", 564)
    wf_frame_find("ksy 布局：帧尾在 562", 562)

    print("D2) incre / multi 展开：旧代码把 multi 字段广播到每个事件并加 1 递增")
    n, step = 3, 12
    plen = 44 + n * 20
    _, _, buf = build("grid1x_ft_packet", plen, n, 20)
    old = old_parse(buf, "grid1x_ft_packet", plen, n, step)
    pk = new_parse(buf, "grid1x_ft_parser", ".ft").packets[0]
    print(f"  旧 event_number = {np.asarray(old['event_number']).ravel().tolist()}"
          f"（每个事件一个值，= 基址+i）")
    print(f"  新 event_number = {pk.event_number}（包级单值；事件级字段只有 events[] 里那 7 个）")

    print("D3) IV/VBR 字节序：XML 字段标注 endian=MSB，旧调用示例却传 endian='LSB'")
    _, _, iv = build("iv_packet", 412)
    o_msb = np.asarray(old_parse(iv, "iv_packet", 412, endian="MSB")["iv"]).ravel()[:4]
    o_lsb = np.asarray(old_parse(iv, "iv_packet", 412, endian="LSB")["iv"]).ravel()[:4]
    n_be = np.asarray(new_parse(iv, "iv_parser", ".iv").to_records()[0]["iv"]).ravel()[:4]
    print(f"  旧 endian=MSB -> {o_msb.tolist()}")
    print(f"  旧 endian=LSB -> {o_lsb.tolist()}   (每个字段都带 endian=MSB，全局 LSB 被覆盖)")
    print(f"  新 ksy (be)   -> {n_be.tolist()}")

    print("D4) check_sum / SUPPORT 覆盖情况")
    p_iv = new_parse(iv, "iv_parser", ".iv")
    v_iv = Validator(p_iv)
    v_iv.process()
    print(f"  .iv 在 crc32 的 SUPPORT 里，但 ksy 无 crc 字段 -> "
          f"checked={v_iv.checked} dropped={v_iv.dropped}（静默跳过）")
    _, _, lv = build("lvds_packet", 2048)
    v_lv = Validator(new_parse(lv, "lvds_parser", ".lvds"))
    v_lv.process()
    print(f"  LVDS ksy 有 check_sum（XML: skip0=4 byte=2，XOR 语义）-> "
          f"旧代码只在字段名为 'bcc' 时才校验、新 Validator 只看 crc* 前缀 -> "
          f"checked={v_lv.checked}（两侧都没实现）")


if __name__ == "__main__":
    main()
