# -*- mode: yaml -*-
meta:
  id: iv_packet
  title: GRID IV 数据包（412B）
  application: GRID Payload Monitor
  file-extension: iv
  endian: be
  ks-version: "0.9"
doc: |
  IV 数据包（来源: xml/grid_packet.xml 的 <iv_packet>；grid_parser_ref/yingtian_packet.xml
  中同名字段偏移一致，无版本歧义）。

  ## 结构（定长 412 字节）
    0..4     header = 0x29416C8E
    4..404   iv：200 个 u2（IV 扫描采样）
    404..412 8 字节：**两版 XML 都未定义**，本文件记为 `reserved`
    → 4 + 200*2 + 8 = 412 ✓

  ## 载荷解读（来自原厂分析代码 grid_parser_ref/analysis_grid_data.py）
    200 个 u2 按 `reshape(points=25, channel=4, 2)` 解读：25 个偏压点 × 4 通道 × (V, I)；
    换算（scan_type='iv'）:
        Rval     = 49.9*2e5/(2e5+49.9)
        current  = 2.5 * I / 4096 / (499 + Rval)          [A]
        voltage  = 20.57 * 2.5 * V / 4096 - current * 499 [V]
    本文件保持**扁平的 u2 数组**（不改变输出形状）；解读/换算放在分析层做。

  ## 校验（语义级）
    - ⚠ 需要确认：`crc_reference.md`（《使用说明》附 1）说 **CRC32（CRC-32C）适用于
      IV / VBR 数据**，但两版参考 XML 在 iv/vbr 包里**都没有定义 CRC 字段**；
      CRC-32C 实际出现在 grid_parser_ref/yingtian_packet.xml 的 `<udp_packet>`（CRC@32）。
      → 本文件不声明 crc 字段，`src/validator.py` 会跳过校验（`checked` 不增加）。
      若确认 404..412 中的前 4 字节就是 CRC-32C，只需：
        1) 把 `reserved` 拆成 `crc32: u4` + `reserved: size: 4`；
        2) 加 instances `crc_tail: 4`、`crc_bytes: 4`、`crc_algo: crc32`；
        3) 重新编译（conf 顶层 CRC_ALGO 的 crc32 已 SUPPORT `.iv`/`.vbr`）。
seq:
  - id: header
    contents: [0x29, 0x41, 0x6c, 0x8e]
    doc: 帧头 0x29416C8E（contents 强校验）
  - id: iv
    type: u2
    repeat: expr
    repeat-expr: 200
    doc: 200 个 IV 采样值（= 25 点 × 4 通道 × (V,I)）
  - id: reserved
    size: 8
    doc: "XML 未定义的 8 字节（404..412）；可能是 CRC32(CRC-32C)+占位，待确认（见 doc）"
