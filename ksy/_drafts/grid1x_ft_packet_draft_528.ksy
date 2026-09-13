meta:
  id: grid1x_ft_packet_draft_528
  endian: be
  file-extension: ft
doc: |
  ⚠ 历史草稿，**勿使用**、**不参与编译**（compile_ksy.py 跳过 _drafts/）。

  内容：把 1x FT 描述成 **528 字节定长帧**：固定头 28B（无 timestamp_bf、无 int_start1..int_end2）、
  事件 41 个 × 12B（timestamp u8 + data_max + data_base，**无逐事件 crc/tail**）、
  末尾单个 buff_full_count + crc + tail。
  - 与 xml/grid_packet.xml 的 584B/逐事件 crc+tail 不一致；也与 grid1x_hk 的既有写法不一致。
  - `in/sample.ft`(84B) 用 grid 版解读时字段值才是干净的连续计数（1,2,3…），故本稿被取代。
  - 它对应的是旧代码 `vary_repeat` 公式（CRC = 2 + base_start + N*multi_step）那种"尾部块"解读，
    该公式只在 multi_step=12 时自洽。

  权威定义：`ksy/grid1x/grid1x_ft_packet.ksy`（grid 版，逐事件 crc/tail）与
  `ksy/grid1x/grid1x_ft_packet_yingtian.ksy`（yingtian 版，u8 时间戳 + 末尾单个 crc/tail）。
seq:
  - id: frames
    type: frame
    repeat: eos
types:
  event:
    seq:
      - id: timestamp
        type: u8
      - id: data_max
        type: u2
      - id: data_base
        type: u2
  frame:
    seq:
      - id: header
        type: u4
        valid:
          eq: 0x1c1c2288
      - id: utc
        type: u4
      - id: pps_for_utc
        type: u4
      - id: timestamp_for_pps_for_utc
        type: u8
      - id: channel_n
        type: u2
      - id: event_number
        type: u4
      - id: pkg_event_num
        type: u2
      - id: events
        type: event
        repeat: expr
        repeat-expr: 41
      - id: buff_full_count
        type: u2
      - id: crc
        type: u2
      - id: tail
        type: u4
        contents: [0xcc, 0x11, 0x88, 0x22]
    instances:
      body_data:
        pos: 0
        type: u1
        repeat: expr
        repeat-expr: 522
      crc_value:
        value: crc