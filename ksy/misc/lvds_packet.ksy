# -*- mode: yaml -*-
meta:
  id: lvds_packet
  title: GRID LVDS 数据包（2048B）
  application: GRID Payload Monitor
  file-extension: lvds
  endian: be
  ks-version: "0.9"
doc: |
  LVDS 数据包（来源: xml/grid_packet.xml 的 <lvds_packet>；仅此一版参考，无版本歧义）。

  ## 结构（定长 2048 字节）
    0..4     header = 0xEB905716
    4..6     data_len（u2）
    6..8     dev_id（u2）
    8..10    frame_id（u2）
    10..2042 data：2032 字节
    2042..2044 check_sum（u2）
    2044..2048 tail = 0x10BD59BF
    → 10 + 2032 + 2 + 4 = 2048 ✓

  ## 校验（语义级）
    - `check_sum`：XML 标注 `skip0=4 skip1=0 byte=2` → **XOR（BCC）语义**：
      从偏移 4 起逐个异或到 check_sum 之前，结果与 check_sum 比对。
    - ⚠ 尚未实现：旧 `parse_grid_data` 只在字段名恰好叫 `bcc` 时才做 BCC 校验（这里叫
      `check_sum`），`src/validator.py` 目前只识别 `crc*` 前缀字段 → 目前仅解析、不校验。
      若要启用：给 conf 的 CRC_ALGO 增加一个 `xor8`/`bcc` 算法插件，并在 SUPPORT 里加 `.lvds`
      （实现方式参考 src/checks/crc16_ccitt.py，只需返回 1 字节 XOR 值）。
seq:
  - id: header
    contents: [0xeb, 0x90, 0x57, 0x16]
    doc: 帧头 0xEB905716（contents 强校验）
  - id: data_len
    type: u2
    doc: 数据长度（载荷固定 2032 字节，本字段仅记录）
  - id: dev_id
    type: u2
    doc: 设备 ID
  - id: frame_id
    type: u2
    doc: 帧 ID
  - id: data
    type: u1
    repeat: expr
    repeat-expr: 2032
    doc: "载荷数据（2032 字节；如嫌 JSON 体积大，可改为 `size: 2032` 输出十六进制串）"
  - id: check_sum
    type: u2
    doc: "校验和（XOR/BCC，从偏移 4 起算；XML: skip0=4 skip1=0 byte=2）⚠ 当前未实现校验"
  - id: tail
    contents: [0x10, 0xbd, 0x59, 0xbf]
    doc: 帧尾 0x10BD59BF（contents 强校验）
