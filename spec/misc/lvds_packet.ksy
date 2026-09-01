# -*- mode: yaml -*-
meta:
  id: lvds_packet
  title: GRID LVDS 数据包
  application: GRID Payload Monitor
  endian: be
  ks-version: "0.9"
doc: |
  LVDS 数据包（源: xml/grid_packet.xml 的 <lvds_packet>）。
  - packet_len=2048, 帧头 0xEB 0x90 0x57 0x16, 帧尾 0x10 0xBD 0x59 0xBF
  - 布局核对: 10 + 2032 + 2 + 4 = 2048 ✓
seq:
  - id: header
    type: u4
    doc: 帧头 0xEB905716
  - id: data_len
    type: u2
    doc: 数据长度
  - id: dev_id
    type: u2
    doc: 设备 ID
  - id: frame_id
    type: u2
    doc: 帧 ID
  - id: data
    type: u1
    repeat: expr
    repeat-expr: 2032
    doc: 载荷数据（2032 字节）
  - id: check_sum
    type: u2
    doc: "校验和（XML: skip0=4 skip1=0 byte=2）"
  - id: tail
    type: u4
    doc: 帧尾 0x10BD59BF
