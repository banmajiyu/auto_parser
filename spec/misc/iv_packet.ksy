# -*- mode: yaml -*-
meta:
  id: iv_packet
  title: GRID IV 数据包
  application: GRID Payload Monitor
  endian: be
  ks-version: "0.9"
doc: |
  IV 数据包（源: xml/grid_packet.xml 的 <iv_packet>）。
  - packet_len=412, 帧头 0x29 0x41 0x6C 0x8E
  - 布局: 4 + 200*2 + 填充8 = 412 ✓（缺省字段默认填充占位）
seq:
  - id: header
    type: u4
    doc: 帧头 0x29416C8E
  - id: iv
    type: u2
    repeat: expr
    repeat-expr: 200
    doc: 200 个 IV 采样值
  - id: padding
    size: 8
    doc: 占位/填充（XML 未定义字段，默认填充占位，凑齐 packet_len=412）
