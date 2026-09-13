# -*- coding: utf-8 -*-
"""端到端验证（迁移后）：
  1) grid1x_hk_packet_178 + Validator 解析 test/sample.hk（517×178B）→ 期望 CRC 全部通过
  2) WF 修正验证：按 XML 规则把 CRC 写到 562 → 期望通过；按旧 ksy 写到 560 → 期望被丢

用法: python script/verify_e2e.py
"""
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.parser import Parser              # noqa: E402
from src.validator import Validator        # noqa: E402
from src.checks.crc16_ccitt import crc16_ccitt   # noqa: E402

print("=== 1) 178B HK（test/sample.hk） ===")
entry178 = {"NAME": "hk178", "TYPE": ".hk", "MODULE": "grid1x.grid1x_hk_packet_178",
            "CLASS": "Grid1xHkPacket178", "PACKET_LEN": 178}
p = Parser(entry178, str(ROOT / "test" / "sample.hk"))
v = Validator(p)
recs = v.process()
print(f"  packets={len(p.packets)} unparsed={p.unparsed} trailing={p.trailing}")
print(f"  Validator: checked={v.checked} dropped={v.dropped} 写出记录={len(recs)}")
r0 = recs[0]
print(f"  第0包: utc_time={r0['utc_time']} sipm_temp0={r0['sipm_temp0']} "
      f"saa_judge_method={r0['saa_judge_method']} gps_status={r0['gps_status']}")

print("\n=== 2) WF 修正（合成包，包尾帧尾必须在校验区间之外） ===")
head = bytes.fromhex("2e2e33ff")
for label, crc_at in (("XML 规则 CRC@562", 562), ("旧 ksy 布局 CRC@560", 560)):
    b = bytearray(((i * 7 + 3) & 0xFF) for i in range(568))
    b[0:4] = head
    b[26:28] = (256).to_bytes(2, "big")
    b[564:568] = bytes.fromhex("22eeff33")
    crc = crc16_ccitt(bytes(b[:crc_at]))
    b[crc_at:crc_at + 2] = crc.to_bytes(2, "big")
    dd = Path(tempfile.mkdtemp())
    f = dd / "x.wf"
    f.write_bytes(bytes(b))
    entry = {"NAME": "wf", "TYPE": ".wf", "MODULE": "grid1x.grid1x_wf_packet",
             "CLASS": "Grid1xWfPacket", "PACKET_LEN": 568}
    pw = Parser(entry, str(f))
    vw = Validator(pw)
    vw.process()
    tail_ok = pw.packets[0].tail == bytes.fromhex("22eeff33")
    print(f"  {label}: tail 解析={'0x22EEFF33 ✓' if tail_ok else '✗'}  "
          f"checked={vw.checked} dropped={vw.dropped}")
