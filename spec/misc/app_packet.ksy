# -*- mode: yaml -*-
meta:
  id: app_packet
  title: GRID APP 分帧数据包
  application: GRID Payload Monitor
  endian: be
  ks-version: "0.9"
doc: |
  APP 分帧数据包（源: xml/grid_packet.xml 的 <app_packet>）。
  - 帧头 0x47 0x52 0x49 0x44 (ASCII "GRID")
  - 变长包: 固定头 18 字节 + data(data_len 字节) + check_sum(2) + tail(4)
  - 注意: XML 的 packet_len="10" 与固定字段实际 18 字节不符，疑为占位值；实际长度 = 18 + data_len + 6
seq:
  - id: header
    type: u4
    doc: 帧头 0x47524944 ("GRID")
  - id: frame_id
    type: u4
    doc: 帧序号
  - id: total_frame
    type: u4
    doc: 总帧数
  - id: frame_type
    type: u1
    doc: 帧类型
  - id: file_num
    type: u1
    doc: 文件号
  - id: data_len
    type: u4
    doc: 数据长度
  - id: data
    size: data_len
    doc: 数据体（变长）
  - id: check_sum
    type: u2
    doc: "校验和（XML: skip0=4 skip1=0 byte=2）"
  - id: tail
    type: u4
    doc: 帧尾
