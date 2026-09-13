# -*- mode: yaml -*-
meta:
  id: app_packet
  title: GRID APP 分帧数据包（变长）
  application: GRID Payload Monitor
  file-extension: app
  endian: be
  ks-version: "0.9"
doc: |
  GRID APP 分帧数据包（来源: xml/grid_packet.xml 的 <app_packet>，
  与 grid_parser_ref/yingtian_packet.xml 的同名包一致）。

  ## 结构（变长包，PACKET_LEN = 0）
    header(4 "GRID") + frame_id(4) + total_frame(4) + frame_type(1) + file_num(1)
    + data_len(4) + data(data_len 字节) + check_sum(2) + tail(4)
    → 实际长度 = 18 + data_len + 6
    - XML 的 `packet_len="10"` 与固定字段实际 18 字节不符，是占位值；
      旧解析函数也没有实现 `vary_tag`，因此 app 只能按本文件的规则解析。
    - `in/sample.app`（32 字节）实测吻合：data_len=8 → 18+8+6 = 32；
      该样本的 check_sum=0xABCD、tail=0xDEADBEEF 是合成值（非真实校验）。

  ## 校验（语义级）
    - `check_sum`：XML 标注 `skip0=4 skip1=0 byte=2`，即 **XOR（BCC）语义** ——
      从偏移 4 起异或到 check_sum 前，结果与 check_sum 比对（16 位，高字节通常为 0）。
    - ⚠ 尚未实现：旧 `parse_grid_data` 只在字段名恰好为 `bcc` 时才做 BCC 校验，
      而这里叫 `check_sum`；`src/validator.py` 目前只识别 `crc*` 前缀字段。
      → 该字段目前仅解析、不校验。若需要，可给 Validator 增加一个 `bcc` 算法插件
      （`XOR` over [skip0, 包尾-tail)）并在 conf 的 CRC_ALGO 里登记。
seq:
  - id: header
    contents: [0x47, 0x52, 0x49, 0x44]
    doc: 帧头 "GRID"（0x47524944）
  - id: frame_id
    type: u4
    doc: 帧序号
  - id: total_frame
    type: u4
    doc: 总帧数
  - id: frame_type
    type: u1
    doc: 帧类型（XML 未给出取值表；如需可补 enums）
  - id: file_num
    type: u1
    doc: 文件号
  - id: data_len
    type: u4
    doc: 数据体长度（字节）
  - id: data
    size: data_len
    doc: 数据体（变长，输出为十六进制串）
  - id: check_sum
    type: u2
    doc: "校验和（XOR/BCC，从偏移 4 起算；XML: skip0=4 skip1=0 byte=2）⚠ 当前未实现校验"
  - id: tail
    type: u4
    doc: 帧尾（XML 未给出固定值，故不做 contents 强校验）
