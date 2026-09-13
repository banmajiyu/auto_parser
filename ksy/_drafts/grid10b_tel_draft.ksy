meta:
  id: grid10b_tel_draft
  endian: be
doc: |
  ⚠ 历史草稿（原名 ksy/wave.ksy），**勿使用**、**不参与编译**（compile_ksy.py 跳过 _drafts/）。

  内容：73 字节/帧，帧头写成 0x47524944("GRID")，字段却是遥测(tel)字段（且没有 current_can_bus），
  末尾是 `sum`(u2)。
  - 既不是 xml/grid_packet.xml 的 <grid1x_wf_packet>，也不是 <app_packet>，
    也不是 10b/11B 的 tel（88B/96B）
  - 帧长 73 不是 8 的倍数（与《使用说明》"凑成 8 的倍数、匹配 CAN 帧"的说法矛盾）
  → 来源不明（疑似早期 tel 草稿或误命名），保留仅供追溯。

  权威定义：波形见 `ksy/grid1x/grid1x_wf_packet.ksy`；遥测见
  `ksy/grid10b/grid10b_tel_packet.ksy` 与 `ksy/grid11b/grid11b_telemetry_packet.ksy`。
seq:
  - id: frames
    type: frame
    repeat: eos
types:
  frame:
    seq:
      - id: header
        type: u4
        valid:
          eq: 0x47524944
      - id: telemetry_count
        type: u1
      - id: cmd_count
        type: u1
      - id: latest_received_cmd
        type: u1
      - id: latest_received_cmd_progress
        type: u1
      - id: latest_complete_cmd
        type: u1
      - id: latest_complete_cmd_arg
        type: u4
      - id: latest_complete_cmd_exit
        type: u1
      - id: utc_time
        type: u4
      - id: ecu_cpu_tempratrue
        type: s1
      - id: daq_temperature_i2c1_0x49
        type: s1
      - id: system_power
        type: u2
      - id: system_input_voltage
        type: u2
      - id: file_upload_progress
        type: u1
      - id: file_upload_check
        type: u1
      - id: normal_or_backup
        type: u1
      - id: storage_valid
        type: u2
      - id: pl_version
        type: u1
      - id: app_version
        type: u1
      - id: log_index
        type: u1
      - id: sci_data_index
        type: u1
      - id: sample_mode
        type: u1
      - id: data_transfer_package_count
        type: u1
      - id: saa_status
        type: u1
      - id: entered_saa_count
        type: u1
      - id: sipm_voltage_ch0
        type: u2
      - id: sipm_current_ch0
        type: u2
      - id: sipm_temperature_ch0
        type: u2
      - id: sipm_voltage_ch1
        type: u2
      - id: sipm_current_ch1
        type: u2
      - id: sipm_temperature_ch1
        type: u2
      - id: sipm_voltage_ch2
        type: u2
      - id: sipm_current_ch2
        type: u2
      - id: sipm_temperature_ch2
        type: u2
      - id: sipm_voltage_ch3
        type: u2
      - id: sipm_current_ch3
        type: u2
      - id: sipm_temperature_ch3
        type: u2
      - id: count_rate0
        type: u2
      - id: count_rate1
        type: u2
      - id: count_rate2
        type: u2
      - id: count_rate3
        type: u2
      - id: sipm_hot_flag
        type: u1
      - id: heat_protect_threshold
        type: u1
      - id: sum
        type: u2
    instances:
      body_data:
        pos: 0
        type: u1
        repeat: expr
        repeat-expr: 71