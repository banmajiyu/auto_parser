# -*- mode: yaml -*-
meta:
  id: vbr_packet
  title: GRID VBR 数据包（412B）
  application: GRID Payload Monitor
  file-extension: vbr
  endian: be
  ks-version: "0.9"
doc: |
  VBR 数据包（来源: xml/grid_packet.xml 的 <vbr_packet>；grid_parser_ref/yingtian_packet.xml
  中同名字段偏移一致，无版本歧义）。

  ## 结构（定长 412 字节）
    0..4     header = 0x18305B7D
    4..404   vbr：200 个 u2（VBR 扫描采样）
    404..412 8 字节：**两版 XML 都未定义**，本文件记为 `reserved`
    → 4 + 200*2 + 8 = 412 ✓

  ## 与 IV 的唯一差别
    header magic（0x18305B7D vs 0x29416C8E）与字段名；换算（scan_type='vbr'）:
        Rval     = 2e5
        current  = 2.5 * I / 4096 / (499 + Rval)          [A]
        voltage  = 20.57 * 2.5 * V / 4096 - current * 499 [V]

  ## ⚠ 历史草稿的坑（ksy/misc/vbr_packet.ksy 旧版，已重写）
    1. 旧稿 `doc: |` 的内容没有缩进 → **YAML 语法错误**，根本无法编译/加载；
    2. 旧稿 header 写成 `contents: [0x18, 0x30, 0x5b, **0x7b**]`，而两版 XML 都是 **0x7d**；
       `contents` 是强校验，真机数据会直接被判非法。本文件已按 0x7D 修正。

  ## 校验（语义级）
    - 与 IV 相同：两版 XML 未定义 CRC 字段 → Validator 跳过（见 `iv_packet.ksy` 的说明）。
seq:
  - id: header
    contents: [0x18, 0x30, 0x5b, 0x7d]
    doc: 帧头 0x18305B7D（contents 强校验）
  - id: vbr
    type: u2
    repeat: expr
    repeat-expr: 200
    doc: 200 个 VBR 采样值（= 25 点 × 4 通道 × (V,I)）
  - id: reserved
    size: 8
    doc: "XML 未定义的 8 字节（404..412）；可能是 CRC32(CRC-32C)+占位，待确认"
