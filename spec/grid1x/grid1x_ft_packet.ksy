# -*- mode: yaml -*-
meta:
  id: grid1x_ft_packet
  title: GRID-1X 命中 (FT) 数据包
  application: GRID Payload Monitor
  endian: be
  ks-version: "0.9"
doc: |
  GRID-1X 命中(FT)数据包（源: xml/grid_packet.xml 的 <grid1x_ft_packet>）。
  - 帧头 0x1C 0x1C 0x22 0x88, 帧尾 0xCC 0x11 0x88 0x22
  - 结构: 固定头 44 字节 + 重复事件块（事件数由 pkg_event_num 决定）
  - 每个事件 20 字节 = 14 字节数据 + crc(2) + tail(4)
  - 事件号 event_number 标注 incre=1（逐事件递增）
  - 说明: packet_len=584 对应 pkg_event_num=27 的情形；实际长度 = 44 + pkg_event_num*20
seq:
  - id: header
    type: u4
    doc: 帧头 0x1C1C2288
  - id: utc
    type: u4
    doc: UTC 时间戳
  - id: pps_for_utc
    type: u4
    doc: UTC 对应的 PPS 计数
  - id: timestamp_for_pps
    type: u8
    doc: PPS 对应时间戳
  - id: timestamp_bf
    type: u8
    doc: 缓冲前时间戳
  - id: channel_n
    type: u2
    doc: 通道号
  - id: event_number
    type: u4
    doc: 事件号（逐事件递增 incre=1）
  - id: pkg_event_num
    type: u2
    doc: 包内事件数（决定事件重复次数）
  - id: int_start1
    type: u2
    doc: 积分起始 1
  - id: int_end1
    type: u2
    doc: 积分结束 1
  - id: int_start2
    type: u2
    doc: 积分起始 2
  - id: int_end2
    type: u2
    doc: 积分结束 2
  - id: events
    type: event
    repeat: expr
    repeat-expr: pkg_event_num
    doc: 重复事件块（数量 = pkg_event_num，每事件 20 字节含 CRC/tail）
types:
  event:
    doc: 单个命中事件（20 字节 = 14 数据 + crc + tail）
    seq:
      - id: timestamp
        type: u4
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
      - id: crc
        type: u2
        doc: "CRC16（XML: vary_repeat 基址 44 偏移 2，计算时跳过首尾 skip0=0 skip1=0）"
      - id: tail
        type: u4
        doc: "帧尾 0xCC118822（XML: vary_repeat 基址 44 偏移 4）"
