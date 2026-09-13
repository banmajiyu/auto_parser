# -*- mode: yaml -*-
meta:
  id: grid1x_es_packet
  title: GRID-1X 能量谱 (ES) 数据包
  application: GRID Payload Monitor
  file-extension: es
  endian: be
  ks-version: "0.9"
doc: |
  GRID-1X 能量谱 (ES) 数据包（来源: xml/grid_packet.xml 的 <grid1x_es_packet>；
  grid_parser_ref/yingtian_packet.xml 中同名字段偏移一致，无版本歧义）。

  ## 布局（定长 528 字节）
    0..30    固定头：header(4) utc(4) pps_for_utc(4) timestamp_for_pps(8) channel_n(2)
             event_number(4) l_ranges_num(2) s_sample_num(2)
    30..38   timestamp(u8)
    38..202  l_energy_data：82 个 u2（L 能区）
    202..522 s_energy_data：160 个 u2（S 采样）
    522..524 crc(u2)
    524..528 tail(u4) = 0x33FFCC44

  ## 校验（语义级）
    - CRC16（CRC-16/XMODEM）覆盖 [0, 522)；crc_tail = 6（crc 2 + 帧尾 4）
    - 与旧 parse_grid_data 的 ES 分支一致（旧: start=522, skip0=skip1=0）
seq:
  - id: header
    contents: [0x3f, 0x3f, 0x44, 0xcc]
    doc: 帧头 0x3F3F44CC（contents 强校验）
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
    doc: 事件号（XML 标注 incre=1，逐包递增）
  - id: l_ranges_num
    type: u2
    doc: L 能区数（数组长度固定为 82，本字段仅记录）
  - id: s_sample_num
    type: u2
    doc: S 采样数（数组长度固定为 160，本字段仅记录）
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
    doc: "CRC16（计算时跳过首尾 skip0=0 skip1=0）"
  - id: tail
    contents: [0x33, 0xff, 0xcc, 0x44]
    doc: 帧尾 0x33FFCC44（contents 强校验）
instances:
  # CRC 校验元数据（供 src/validator.py 读取）
  crc_skip0:
    value: 0
    doc: "CRC 计算时从包首跳过的字节数（XML: skip0）"
  crc_skip1:
    value: 0
    doc: "CRC 计算时从结尾向前排除的字节数（XML: skip1）"
  crc_bytes:
    value: 2
    doc: "CRC 字段字节数"
  crc_tail:
    value: 6
    doc: "CRC 字段起点距包尾的字节数（crc 2 + 帧尾 4）"
  body_data:
    pos: 0
    type: u1
    repeat: expr
    repeat-expr: 522
    doc: CRC 覆盖区间 [0, 522) 的字节视图
