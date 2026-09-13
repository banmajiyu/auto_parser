# -*- coding: utf-8 -*-
"""回归对比：同一份合成包，用「迁移前生成的解析器」与「迁移后生成的解析器」各解析一遍，
逐个叶子字段比对，用于确认迁移没有改变解析语义（重命名 / 类型增强 / 有意修正除外）。

用法:
    python script/compare_generated.py <before_dir> <after_dir> [--10b-root DIR]

比对策略：
  - 递归摊平为 [(路径, 值)]，按顺序两两比较（**忽略键名差异**，从而容忍重命名）
  - 值归一化：4/8 字节十六进制串 -> int；scaled 类型（含 raw/converted）-> 取 raw；IntEnum -> int
  - 另外单独报告"键名集合差异"（重命名/新增/删除）
"""
import importlib.util
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import kaitaistruct                                   # noqa: E402
from kaitaistruct import KaitaiStream, BytesIO        # noqa: E402

# name -> dict(mod, cls, plen, head, tail, special, before)
# SPECS: 各种数据包的规格信息
SPECS = {
    "hk":      dict(mod="grid1x/grid1x_hk_packet.py", cls="Grid1xHkPacket", plen=187,
                    head="1a2b3c4d"),
    "hk178":   dict(mod="grid1x/grid1x_hk_packet_178.py", cls="Grid1xHkPacket178", plen=178,
                    head="1a2b3c4d"),
    "ft":      dict(mod="grid1x/grid1x_ft_packet.py", cls="Grid1xFtPacket", plen=84,
                    head="1c1c2288", special="ft"),
    "ft_yt":   dict(mod="grid1x/grid1x_ft_packet_yingtian.py", cls="Grid1xFtPacketYingtian",
                    plen=584, head="1c1c2288", tail=(580, "cc118822"), special="ft_yt"),
    "wf":      dict(mod="grid1x/grid1x_wf_packet.py", cls="Grid1xWfPacket", plen=568,
                    head="2e2e33ff", tail=(564, "22eeff33")),
    "es":      dict(mod="grid1x/grid1x_es_packet.py", cls="Grid1xEsPacket", plen=528,
                    head="3f3f44cc", tail=(524, "33ffcc44")),
    "tlm":     dict(mod="grid11b/grid11b_telemetry_packet.py", cls="Grid11bTelemetryPacket",
                    plen=96, head="48454144", tail=(92, "5441494c")),
    "hk10b":   dict(mod="grid10b/grid10b_hk_packet.py", cls="Grid10bHkPacket", plen=187,
                    head="1a2b3c4d", before=("hk", "frameseq.py", "Frameseq")),
    "tel10b":  dict(mod="grid10b/grid10b_tel_packet.py", cls="Grid10bTelPacket", plen=88,
                    before=("tel", "frameseq.py", "Frameseq")),
    "iv":      dict(mod="misc/iv_packet.py", cls="IvPacket", plen=412, head="29416c8e"),
    "vbr":     dict(mod="misc/vbr_packet.py", cls="VbrPacket", plen=412, head="18305b7d"),
    "lvds":    dict(mod="misc/lvds_packet.py", cls="LvdsPacket", plen=2048,
                    head="eb905716", tail=(2044, "10bd59bf")),
    "app":     dict(mod="misc/app_packet.py", cls="AppPacket", plen=32,
                    head="47524944", special="app"),
}

def build(spec):
    """按规格生成一个合成包（字节串）"""
    plen = spec["plen"]
    b = bytearray(((i * 7 + 3) & 0xFF) for i in range(plen))
    if spec.get("head"):
        h = bytes.fromhex(spec["head"])
        b[0:len(h)] = h
    if spec.get("tail"):
        off, t = spec["tail"]
        t = bytes.fromhex(t)
        b[off:off + len(t)] = t
    if spec.get("special") == "ft":
        b[34:36] = (2).to_bytes(2, "big")
        for i in range(2):
            b[44 + i * 20 + 16:44 + i * 20 + 20] = bytes.fromhex("cc118822")
    elif spec.get("special") == "ft_yt":
        b[26:28] = (27).to_bytes(2, "big")
    elif spec.get("special") == "app":
        b[14:18] = (8).to_bytes(4, "big")
    return bytes(b)


def load(dirpath: Path, mod_rel: str, tag: str):
    """动态加载指定目录下的模块，返回模块对象；若不存在则返回 None"""
    p = dirpath / mod_rel
    if not p.exists():
        return None
    name = f"g_{tag}_{mod_rel.replace('/', '_')[:-3]}"
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def walk_struct(obj):
    """公共成员；跳过参数化类型的构造形参（scale/offset），与 Parser._member_names 一致。"""
    return {k: v for k, v in vars(obj).items()
            if not k.startswith("_") and k not in ("scale", "offset")}


def norm(v):
    """归一化叶子值：
    - 4/8 字节十六进制串 -> int
    - scaled 类型（含 raw/converted）-> 取 raw
    - IntEnum -> int"""
    if isinstance(v, dict):
        return norm(v["raw"]) if "raw" in v else {k: norm(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [norm(x) for x in v]
    if isinstance(v, bytes):
        return int.from_bytes(v, "big") if len(v) <= 8 else v.hex()
    if isinstance(v, str):
        s = v
        if len(s) in (8, 16) and all(c in "0123456789abcdef" for c in s.lower()):
            return int(s, 16)
        return v
    if isinstance(v, kaitaistruct.KaitaiStruct):
        return {k: norm(x) for k, x in walk_struct(v).items()}
    return v

def flatten(obj, path="", out=None):
    """递归摊平 KaitaiStruct / list / tuple，输出 [(路径, 值)]"""
    if out is None:
        out = []
    if isinstance(obj, kaitaistruct.KaitaiStruct):
        d = walk_struct(obj)
        if not d:
            out.append((path, obj))
            return out
        for k, v in d.items():
            flatten(v, f"{path}.{k}" if path else k, out)
        return out
    if isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            flatten(v, f"{path}[{i}]", out)
        return out
    out.append((path, obj))
    return out


def leaves(rec):
    """摊平记录，返回叶子 [(路径, 归一化值)]"""
    return [(p, norm(v)) for p, v in flatten(rec)]


def parse(mod, cls_name, buf):
    """用指定模块的指定类解析字节串，返回 KaitaiStruct 对象"""
    obj = getattr(mod, cls_name)(KaitaiStream(BytesIO(buf)))
    if hasattr(obj, "frames"):                  # 旧 frameseq 写法：取第一帧
        obj = obj.frames[0]
    return obj


def main():
    """ 对比迁移前后生成的解析器解析同一份合成包的结果，报告叶子值差异与键名差异 """
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    before_dir = Path(args[0]) if args else Path(r"C:\Users\13988\AppData\Local\Temp\generated_before")
    after_dir = Path(args[1]) if len(args) > 1 else Path(r"C:\Users\13988\AppData\Local\Temp\gen_after")
    root_10b = Path(sys.argv[sys.argv.index("--10b-root") + 1]) if "--10b-root" in sys.argv else None
    print(f"before = {before_dir}\nafter  = {after_dir}\n")
    total = 0
    for name, spec in SPECS.items():
        bspec = spec.get("before")
        if bspec and root_10b:
            sub, mrel, bcls_name = bspec
            mb = load(root_10b / sub, mrel, f"b_{name}")
        else:
            mb = load(before_dir, spec["mod"], f"b_{name}")
            bcls_name = spec["cls"]
        if mb is None:
            print(f"[{name}] 跳过：迁移前没有对应解析器")
            continue
        ma = load(after_dir, spec["mod"], f"a_{name}")
        if ma is None:
            print(f"[{name}] ✗ 迁移后缺少 {spec['mod']}")
            total += 1
            continue
        buf = build(spec)
        try:
            rb = parse(mb, bcls_name, buf)
        except Exception as e:
            print(f"[{name}] ✗ 迁移前解析异常: {type(e).__name__}: {e}")
            continue
        try:
            ra = parse(ma, spec["cls"], buf)
        except Exception as e:
            print(f"[{name}] ✗ 迁移后解析异常: {type(e).__name__}: {e}")
            total += 1
            continue
        lb, la = leaves(rb), leaves(ra)
        diffs = [(i, pb, vb, pa, va) for i, ((pb, vb), (pa, va)) in enumerate(zip(lb, la))
                 if vb != va]
        renamed = len({p for p, _ in lb} ^ {p for p, _ in la})
        flag = "✓ 值完全一致" if not diffs and not renamed else ""
        print(f"[{name}] 叶子 {len(lb)}/{len(la)}  值差异 {len(diffs)}  键名差异 {renamed}  {flag}")
        for i, pb, vb, pa, va in diffs[:5]:
            print(f"     #{i} {pb} = {str(vb)[:26]}  ->  {pa} = {str(va)[:26]}")
        if len(diffs) > 5:
            print(f"     ... 另有 {len(diffs) - 5} 处")
        total += len(diffs)
    print(f"\n合计值差异 {total} 处（重命名/contents 化/scaled 化/WF 修正都属于预期）")


if __name__ == "__main__":
    main()
