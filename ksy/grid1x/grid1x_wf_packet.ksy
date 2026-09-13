# -*- mode: yaml -*-
meta:
  id: grid1x_wf_packet
  title: GRID-1X 波形 (WF) 数据包
  application: GRID Payload Monitor
  file-extension: wf
  endian: be
  ks-version: "0.9"
doc: |
  GRID-1X 波形 (WF) 数据包（来源: xml/grid_packet.xml 的 <grid1x_wf_packet>，
  并与 grid_parser_ref/yingtian_packet.xml 交叉核对过 —— 两版**字段偏移完全一致**）。

  ## 布局（定长 568 字节）
    0..28    固定头：header(4) utc(4) pps_for_utc(4) timestamp_for_pps(8) channel_n(2)
             event_number(4) sample_length(2)
    28..540  waveform_data：256 个 u2 采样（= sample_length * 2；本包型固定 256）
    540..558 尾块前半：timestamp(8) data_max(2) data_base(2) data_sum(4) data_ccm(2)
    558..560 **reserved(2)**：两版 XML 都未列出这 2 字节（旧代码的字段表就停在这里）
    560..562 bufff_full_count(u2)
    562..564 crc(u2)
    564..568 tail(u4) = 0x22EEFF33（帧尾，且必须是包尾最后 4 字节）

  ## ⚠ 修正记录（2026-09 核对）
    早期 `spec/grid1x_wf_packet.ksy` 把 2 字节占位放在**包尾**，导致
    bufff_full_count/CRC/tail 整体前移 2 字节（CRC@560、tail@562..566），后果：
      - 帧尾字段读到的是 CRC/占位而非 0x22EEFF33；
      - CRC 覆盖区间变成 [0,560) 而真值是 [0,562) → **所有 WF 包都会被校验失败丢弃**；
      - 旧定帧正则 `head.{560}tail`（要求帧尾在包尾）在真实文件上只能匹配 0 个包。
    两份参考 XML 的字段表都指向 558..560 为未列出字节、CRC@562，故此处按参考修正。

  ## 校验（语义级）
    - CRC16（CRC-16/XMODEM）覆盖 [0, 562)；crc_tail = 6（crc 2 + 帧尾 4）
seq:
  - id: header
    contents: [0x2e, 0x2e, 0x33, 0xff]
    doc: 帧头 0x2E2E33FF（contents 强校验）
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
  - id: sample_length
    type: u2
    doc: "采样长度；本包型固定 256（波形区 = sample_length * 2 字节，旧代码据此动态取长度）"
  - id: waveform_data
    type: u2
    repeat: expr
    repeat-expr: 256
    doc: 波形数据（256 个采样）
  - id: timestamp
    type: u8
    doc: "事件时间戳（尾块开始，XML: vary_wf 基址 = 540）"
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
    doc: 两份参考 XML 都未列出的 2 字节（558..560；勿与包尾占位混淆）
  - id: bufff_full_count
    type: u2
    doc: 缓冲满计数（原 XML 拼写 bufff_full_count；yingtian 版名为 buff_full_cnt）
  - id: crc
    type: u2
    doc: "CRC16（计算时跳过首尾 skip0=0 skip1=0）"
  - id: tail
    contents: [0x22, 0xee, 0xff, 0x33]
    doc: 帧尾 0x22EEFF33（必须是包尾最后 4 字节，旧定帧正则依赖它）
instances:
  # CRC 校验元数据（供 src/validator.py 读取；声明后优先于 conf 的默认值）
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
    repeat-expr: 562
    doc: CRC 覆盖区间 [0, 562) 的字节视图
