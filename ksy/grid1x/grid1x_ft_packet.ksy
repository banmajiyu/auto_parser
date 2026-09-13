# -*- mode: yaml -*-
meta:
  id: grid1x_ft_packet
  title: GRID-1X 命中 (FT) 数据包（grid 版：逐事件 CRC + 帧尾）
  application: GRID Payload Monitor
  file-extension: ft
  endian: be
  ks-version: "0.9"
doc: |
  GRID-1X 命中 (FT) 数据包 —— **grid 版**（来源: xml/grid_packet.xml 的 <grid1x_ft_packet>，
  与原 grid_parser_ref/parse_grid_data.py 的 ft 分支对应）。

  ## 结构（变长包，PACKET_LEN = 0）
    - 固定头 44 字节
    - pkg_event_num 个事件，每个 20 字节 = 14 字节数据 + crc(2) + 帧尾(4)
    - 包长 = 44 + pkg_event_num * 20（XML 的 packet_len=584 对应 pkg_event_num=27）

  ## 版本说明（重要）
    - 本文件 = **grid 版**：帧尾 0xCC118822 出现在**每个事件**末尾。
      `in/sample.ft`（84B = 44 + 2*20）实测吻合：两个事件的尾都是 0xCC118822，
      事件数据为 1,2,3… 的连续计数，故 1x 真机最可能用这一版。
    - 另一版见 `grid1x_ft_packet_yingtian.ksy`（来源 grid_parser_ref/yingtian_packet.xml）：
      固定头 36B + 每事件 20B（18B 数据，含 u8 时间戳）+ 末尾单个 crc/tail。
    - **两版对"包尾"的认识是一致的**：packet_len=584 时 CRC 都在 578、帧尾都在 580..584
      （因为 44+14 = 36+22 = 58，即最后一个事件的数据起点偏移相同）。
    - 旧代码的 `vary_repeat` 公式（CRC 起点 = 属性值 + base_start + N*multi_step）只有在
      multi_step=12 时自洽；对 20 字节/事件会算到包外（N=3 时得 106 > 包长 104），
      故本文件按 XML 的**字段定义**（crc/tail 在事件内）建模。

  ## 校验（语义级）
    - CRC16（CRC-16/XMODEM，poly 0x1021、init 0）覆盖 **[0, 最后一个事件的 crc 起点)**
    - crc_tail = 6（crc 2 字节 + 帧尾 4 字节）；中间事件的 crc 只解析、不单独校验（与旧代码一致）
seq:
  - id: header
    contents: [0x1c, 0x1c, 0x22, 0x88]
    doc: 帧头 0x1C1C2288（contents 强校验）
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
    doc: 缓冲前时间戳（本版特有；yingtian 版无此字段）
  - id: channel_n
    type: u2
    doc: 通道号
  - id: event_number
    type: u4
    doc: "事件号；XML 标注 incre=1（逐事件递增，旧代码会广播为 基址+i）"
  - id: pkg_event_num
    type: u2
    doc: 包内事件数（决定 events 重复次数）
  - id: int_start1
    type: u2
    doc: 积分起始 1（yingtian 版名为 ccm_start1）
  - id: int_end1
    type: u2
    doc: 积分结束 1（yingtian 版名为 ccm_end1）
  - id: int_start2
    type: u2
    doc: 积分起始 2（yingtian 版名为 ccm_start2）
  - id: int_end2
    type: u2
    doc: 积分结束 2（yingtian 版名为 ccm_end2）
  - id: events
    type: event
    repeat: expr
    repeat-expr: pkg_event_num
    doc: 重复事件块，数量 = pkg_event_num（每事件 20 字节，含本事件的 crc 与帧尾）
types:
  event:
    doc: 单个命中事件（20 字节 = 14 数据 + crc + 帧尾）
    seq:
      - id: timestamp
        type: u4
        doc: 事件时间戳（yingtian 版为 u8）
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
        doc: "CRC16（本事件的 CRC；校验只取最后一个事件的 crc，见 doc 的『校验』一节）"
      - id: tail
        contents: [0xcc, 0x11, 0x88, 0x22]
        doc: 帧尾 0xCC118822（contents 强校验，每个事件都有）
    instances:
      # CRC 校验元数据（Validator 会遍历对象树找 crc_* 实例，写在“带 crc 字段的类型”里）
      crc_skip0:
        value: 0
        doc: "CRC 计算时从包首跳过的字节数（XML: skip0）"
      crc_skip1:
        value: 0
        doc: "CRC 计算时从结尾向前排除的字节数（XML: skip1）"
      crc_bytes:
        value: 2
        doc: "CRC 字段字节数（XML: byte）"
      crc_tail:
        value: 6
        doc: "CRC 字段起点距包尾的字节数（crc 2 + 帧尾 4）"
