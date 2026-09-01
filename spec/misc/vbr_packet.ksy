# -*- mode: yaml -*-
meta:
  id: vbr_packet
  title: GRID VBR 数据包
  application: GRID Payload Monitor
  endian: be
  ks-version: "0.9"
doc: |
  VBR 数据包（源: xml/grid_packet.xml 的 <vbr_packet>）。
  - packet_len=412, 帧头 0x18 0x30 0x5B 0x7D
  - 布局: 4 + 200*2 + 填充8 = 412 ✓（缺省字段默认填充占位）
seq:
  - id: header
    type: u4
    doc: 帧头 0x18305B7D
  - id: vbr
    type: u2
    repeat: expr
    repeat-expr: 200
    doc: 200 个 VBR 采样值
  - id: padding
    size: 8
    doc: 占位/填充（XML 未定义字段，默认填充占位，凑齐 packet_len=412）
