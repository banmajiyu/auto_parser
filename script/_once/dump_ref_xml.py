# -*- coding: utf-8 -*-
"""临时工具：dump 任意参考 XML（如 grid_parser_ref/yingtian_packet.xml）的包布局。

用法: python script/_once/dump_ref_xml.py [xml路径]
"""
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
XML = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "grid_parser_ref" / "yingtian_packet.xml"

root = ET.parse(XML).getroot()
for pkt in root:
    total = int(pkt.attrib.get("packet_len", 0))
    print("=" * 96)
    print(f"<{pkt.tag}>  {dict(pkt.attrib)}")
    base_wf = None
    for et in pkt.findall("./"):
        if et.tag == "waveform_data":
            base_wf = (int(et.find("start").text), int(et.find("size").text),
                       int(et.find("len").text))
    for et in pkt.findall("./"):
        st = et.find("start")
        s = int(st.text)
        note = ""
        if base_wf and "vary_wf" in st.attrib:
            s += base_wf[0] + base_wf[1] * base_wf[2]
        for k in ("vary_repeat", "vary_tag"):
            if k in st.attrib:
                note = f" <{k} base={st.attrib}>"
        size = int(et.find("size").text)
        ln = int(et.find("len").text)
        attrs = "".join(f" {k}={v}" for k, v in {**st.attrib, **et.attrib}.items()
                        if k not in ("vary_wf", "vary_repeat", "vary_tag"))
        print(f"  {et.tag:<26} start={s:<6} size={size:<3} len={ln:<5} end={s + size * ln:<6}{attrs}{note}")
