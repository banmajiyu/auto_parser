# -*- mode: yaml -*-
meta:
  id: grid1x_ft_packet_yingtian
  title: GRID-1X 命中 (FT) 数据包（yingtian 版：u8 时间戳 + 末尾单个 crc/tail）
  application: GRID Payload Monitor
  file-extension: ft
  endian: be
  ks-version: "0.9"
doc: |
  GRID-1X 命中 (FT) 数据包 —— **yingtian 版**（来源: grid_parser_ref/yingtian_packet.xml 的
  <grid1x_ft_packet>，该文件用**绝对偏移**描述，比 grid_packet.xml 的模板更直白）。

  ## 与 grid 版的差异（务必区分版本）
    | | grid 版 (`grid1x_ft_packet.ksy`) | yingtian 版（本文件） |
    |---|---|---|
    | 固定头 | 44B（含 timestamp_bf u8 @20、int_start1..int_end2 @36..44） | 36B（无 timestamp_bf；ccm_start1..ccm_end2 @28..36） |
    | 事件数据 | 14B（timestamp **u4** + max + base + sum + ccm） | 18B（timestamp **u8** + max + base + sum + ccm） |
    | 事件步长 | 20B = 14 + crc2 + tail4 | 20B = 18 + crc2（**每个事件一个 CRC**） |
    | 帧尾 | 每个事件末尾都有 0xCC118822 | 只在包尾出现一次（580..584） |
    | 包长（pkg_event_num=27） | 44 + 27*20 = 584 | 40 + 26*20 + 18 + 2 + 4 = 584 |
    | 末事件 CRC 位置 | 44 + 26*20 + 14 = 578 | 40 + 26*20 + 18 = 578 ← **两版一致** |

  ## 建模依据与不确定处（待真机确认）
    - 源 XML 只列出固定头字段 + 静态 CRC@578 + 包属性 tail=0xCC118822；事件区未给步长。
    - 由“CRC@578 + packet_len=584 + 每事件 18B 数据”反推：固定头实到偏移 36，
      但事件区必须从 40 开始才能让 27 个事件落在 578 → **36..40 这 4 字节源 XML 未列出**，
      本文件记为 `reserved`。
    - 同理，前 pkg_event_num-1 个事件各含 **2 字节未定义**（源 XML 未列出），
      本文件在 event 类型里记为 `reserved`；最后一个事件之后才是 `crc` + `tail`。
    - ⚠ `in/sample.ft`（84B）用 **grid 版**解读时字段值才是干净的连续计数，
      故本文件仅作**版本对照/参考**；如真机数据用本版解读更合理，请反馈后再调整 conf。

  ## 校验（语义级）
    - 与 grid 版一致：CRC16 覆盖 [0, 578)、存入 578..580、帧尾 580..584（crc_tail = 6）
seq:
  - id: header
    contents: [0x1c, 0x1c, 0x22, 0x88]
    doc: 帧头 0x1C1C2288（包属性 head）
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
    doc: "通道号（源 XML: multi=1）"
  - id: event_number
    type: u4
    doc: "事件号（源 XML: multi=1 incre=1）"
  - id: pkg_event_num
    type: u2
    doc: 包内事件数
  - id: ccm_start1
    type: u2
    doc: 积分起始 1（grid 版名为 int_start1）
  - id: ccm_end1
    type: u2
    doc: 积分结束 1（grid 版名为 int_end1）
  - id: ccm_start2
    type: u2
    doc: 积分起始 2（grid 版名为 int_start2）
  - id: ccm_end2
    type: u2
    doc: 积分结束 2（grid 版名为 int_end2）
  - id: reserved
    size: 4
    doc: 源 XML 未列出的 4 字节（36..40）
  - id: events
    type: event
    repeat: expr
    repeat-expr: pkg_event_num - 1
    doc: 前 pkg_event_num-1 个事件（每事件 18B 数据 + 2B 源 XML 未定义字段）
  - id: last_event
    type: event
    doc: 最后一个事件（18B 数据；其后的 crc 即末事件 CRC）
  - id: crc
    type: u2
    doc: "CRC16；覆盖 [0, crc 起点)，即包首到本字段（源 XML: skip0=0 skip1=0）"
  - id: tail
    contents: [0xcc, 0x11, 0x88, 0x22]
    doc: 帧尾 0xCC118822（包属性 tail；整包只出现一次）
types:
  event:
    doc: 事件（18B 数据 + 2B 未定义占位，共 20B 步长）
    seq:
      - id: timestamp
        type: u8
        doc: 事件时间戳（u8；grid 版为 u4）
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
      - id: reserved
        size: 2
        doc: 源 XML 未列出的 2 字节（源 XML 未给事件步长，由 20B 步长反推）
instances:
  # CRC 校验元数据（与 grid 版完全一致；Validator 遍历对象树即可读到）
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
