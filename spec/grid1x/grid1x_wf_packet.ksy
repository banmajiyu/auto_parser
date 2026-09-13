# -*- mode: yaml -*-
meta:
  id: grid1x_wf_packet
  title: GRID-1X 波形 (WF) 数据包
  application: GRID Payload Monitor
  endian: be
  ks-version: "0.9"
doc: |
  GRID-1X 波形数据包（源: xml/grid_packet.xml 的 <grid1x_wf_packet>）。
  - packet_len=568, 帧头 0x2E 0x2E 0x33 0xFF, 帧尾 0x22 0xEE 0xFF 0x33
  - 尾部字段位置基于波形结束（vary_wf 基址 = 28 + 256*2 = 540）
  - 布局: 28 + 512 + 尾块26字节 + 填充2字节 = 568 ✓
seq:
  - id: header
    type: u4
    doc: 帧头 0x2E2E33FF
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
  - id: sample_length
    type: u2
    doc: 采样长度
  - id: waveform_data
    type: u2
    repeat: expr
    repeat-expr: 256
    doc: 波形数据（256 个采样）
  - id: timestamp
    type: u8
    doc: 事件时间戳
  - id: data_max
    type: u2
    doc: 数据最大值
  - id: data_base
    type: u2
    doc: 数据基线
  - id: data_sum
    type: u4
    doc: 数据总和
  - id: data_ccm
    type: u2
    doc: 数据 CCM
  - id: bufff_full_count
    type: u2
    doc: 缓冲满计数（原 XML 拼写 bufff_full_count）
  - id: crc
    type: u2
    doc: CRC16（计算时跳过首尾 skip0=0 skip1=0）
  - id: tail
    type: u4
    doc: 帧尾 0x22EEFF33
  - id: padding
    size: 2
    doc: 占位/填充（XML 未定义字段，默认填充占位，凑齐 packet_len=568）
