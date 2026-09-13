# -*- mode: yaml -*-
meta:
  id: grid1x_es_packet
  title: GRID-1X 能量谱 (ES) 数据包
  application: GRID Payload Monitor
  endian: be
  ks-version: "0.9"
doc: |
  GRID-1X 能量谱数据包（源: xml/grid_packet.xml 的 <grid1x_es_packet>）。
  - packet_len=528, 帧头 0x3F 0x3F 0x44 0xCC, 帧尾 0x33 0xFF 0xCC 0x44
  - 布局核对: 固定头 30 字节 + timestamp(8) + l_energy(82*2) + s_energy(160*2) + crc(2) + tail(4) = 528 ✓
seq:
  - id: header
    type: u4
    doc: 帧头 0x3F3F44CC
  - id: utc
    type: u4
    doc: UTC 时间戳
  - id: pps_for_utc
    type: u4
    doc: UTC 对应的 PPS 计数
  - id: timestamp_for_pps
    type: u8
    doc: PPS 对应时间戳
  - id: channel_n
    type: u2
    doc: 通道号
  - id: event_number
    type: u4
    doc: 事件号（逐包递增 incre=1）
  - id: l_ranges_num
    type: u2
    doc: L 能区数
  - id: s_sample_num
    type: u2
    doc: S 采样数
  - id: timestamp
    type: u8
    doc: 事件时间戳
  - id: l_energy_data
    type: u2
    repeat: expr
    repeat-expr: 82
    doc: L 能量数据（82 个）
  - id: s_energy_data
    type: u2
    repeat: expr
    repeat-expr: 160
    doc: S 能量数据（160 个）
  - id: crc
    type: u2
    doc: CRC16（计算时跳过首尾 skip0=0 skip1=0）
  - id: tail
    type: u4
    doc: 帧尾 0x33FFCC44
