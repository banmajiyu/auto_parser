# -*- mode: yaml -*-
meta:
  id: grid1x_hk_packet_178
  title: GRID-1X HK 遥测包（178 字节版 / yingtian 版）
  application: GRID Payload Monitor
  file-extension: hk
  endian: be
  ks-version: "0.9"
doc: |
  GRID-1X HK（Housekeeping）遥测包 —— **178 字节版**（来源: grid_parser_ref/yingtian_packet.xml
  的 <hk_packet packet_len="178">）。

  ## 版本说明（务必与 187 版区分）
    - `grid1x_hk_packet.ksy` = **187 字节版**（xml/grid_packet.xml）
    - 本文件 = **178 字节版**：GPS/姿态字段完全不同（gps_status / gps_utc_s / gps_orbit_* /
      attitude_* 取代了 187 版的 wgs_84_* / 星敏四元数），且 **少 1 个 u2**：
      178 版没有 `daq_1v5_i_0x48_1`（DAQ 1V5 电流），因此 SiPM 区从 82 前移到 80。
      FEE/DAQ 的**电压**字段偏移在两版完全相同（14..80），只有 SiPM 及其后错开 2 字节。
    - 源 XML 未列出的字节（105、107、114..116、146..148、172..176）在本文件记为 `reserved`。

  ## 实测验证（2026-09-12）
    - `in/sample.hk` = 517 × 178B；按本文件布局 **CRC@176 覆盖 [0,176) 命中 517/517**，
      证明 178B 版布局与 CRC 规则成立（187 版按 187 切会全错）。
    - 该样本 GPS/姿态区基本为 0（无星敏/GPS 数据），故这些字段无法用样本反查。

  ## 换算（按 housekeepping_data_format.md 的 tag 定义，与 187 版一致）
    - sipm_voltage: converted(mV) = raw * 1.25
    - sipm_temp:    converted(摄氏度) = raw * 0.01 - 273.15
    - 其余（含全部 ADC/GPS/姿态字段）保留原始数字量

  ## 校验（语义级）
    - CRC16（CRC-16/XMODEM）覆盖 [0, 176)、存入 176..178（crc_tail = 2）
seq:
  - id: header
    contents: [0x1a, 0x2b, 0x3c, 0x4d]
    doc: 帧头 0x1A2B3C4D（contents 强校验）
  - id: utc_time
    type: u4
    doc: UTC 时间戳（秒）
  - id: cpu_temperature
    type: u2
    doc: CPU 温度数字量
  - id: daq_temperature_i2c1_0x49
    type: u2
    doc: DAQ 温度数字量（I2C1 0x49）
  - id: storage_valid
    type: u2
    doc: "ECU 剩余存储空间, 单位: 1MB"
  # --- FEE 转接板电源监测（与 187 版偏移相同）---
  - id: fee_z5v_v_0x40_1
    type: u2
    doc: FEE +5V 电压
  - id: fee_z5v_i_0x40_1
    type: u2
    doc: FEE +5V 电流
  - id: fee_z2v1_v_0x41_1
    type: u2
    doc: FEE +2.1V 电压
  - id: fee_z2v1_i_0x41_1
    type: u2
    doc: FEE +2.1V 电流
  - id: fee_z5v4_v_0x42_1
    type: u2
    doc: FEE +5.4V 电压
  - id: fee_z5v4_i_0x42_1
    type: u2
    doc: FEE +5.4V 电流
  - id: fee_z5va_v_0x4d_1
    type: u2
    doc: FEE +5VA 电压（0x4D）
  - id: fee_z5va_i_0x4d_1
    type: u2
    doc: FEE +5VA 电流（0x4D）
  - id: fee_5va_v_0x40
    type: u2
    doc: FEE 5VA 电压（0x40）
  - id: fee_5va_i_0x40
    type: u2
    doc: FEE 5VA 电流（0x40）
  - id: fee_1v8a_v_0x41
    type: u2
    doc: FEE +1.8A 电压（0x41）
  - id: fee_1v8a_i_0x41
    type: u2
    doc: FEE +1.8A 电流（0x41）
  - id: fee_3v3_v_0x42
    type: u2
    doc: FEE +3.3V 电压（0x42）
  - id: fee_3v3_i_0x42
    type: u2
    doc: FEE +3.3V 电流（0x42）
  - id: fee_1v8d_v_0x43
    type: u2
    doc: FEE +1.8D 电压（0x43）
  - id: fee_1v8d_i_0x43
    type: u2
    doc: FEE +1.8D 电流（0x43）
  - id: fee_p5va1_v_0x44
    type: u2
    doc: FEE P5VA1 电压（0x44）
  - id: fee_p5va1_i_0x44
    type: u2
    doc: FEE P5VA1 电流（0x44）
  - id: fee_p5va2_v_0x45
    type: u2
    doc: FEE P5VA2 电压（0x45）
  - id: fee_p5va2_i_0x45
    type: u2
    doc: FEE P5VA2 电流（0x45）
  - id: fee_p5va3_v_0x46
    type: u2
    doc: FEE P5VA3 电压（0x46）
  - id: fee_p5va3_i_0x46
    type: u2
    doc: FEE P5VA3 电流（0x46）
  - id: fee_p5va4_v_0x47
    type: u2
    doc: FEE P5VA4 电压（0x47）
  - id: fee_p5va4_i_0x47
    type: u2
    doc: FEE P5VA4 电流（0x47）
  # --- DAQ 电源监测（178 版缺 1V5 电流）---
  - id: daq_1v0_v_0x43_1
    type: u2
    doc: DAQ +1.0V 电压（0x43）
  - id: daq_1v0_i_0x43_1
    type: u2
    doc: DAQ +1.0V 电流（0x43）
  - id: daq_1v8_v_0x44_1
    type: u2
    doc: DAQ +1.8V 电压（0x44）
  - id: daq_1v8_i_0x44_1
    type: u2
    doc: DAQ +1.8V 电流（0x44）
  - id: daq_2v5_v_0x45_1
    type: u2
    doc: DAQ +2.5V 电压（0x45）
  - id: daq_2v5_i_0x45_1
    type: u2
    doc: DAQ +2.5V 电流（0x45）
  - id: daq_3v3_v_0x47_1
    type: u2
    doc: DAQ +3.3V 电压（0x47）
  - id: daq_3v3_i_0x47_1
    type: u2
    doc: DAQ +3.3V 电流（0x47）
  - id: daq_1v5_v_0x48_1
    type: u2
    doc: DAQ +1.5V 电压（0x48）⚠ 178 版到此为止，187 版在其后还有 daq_1v5_i
  # --- SiPM 通道 0-3 ---
  - id: sipm_voltage0
    type: scaled_u2(1.25, 0.0)
    doc: "SiPM 通道0偏压; converted(mV) = raw * 1.25"
  - id: sipm_current0
    type: u2
    doc: SiPM 通道0电流（原始 uA）
  - id: sipm_temp0
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道0温度; converted(摄氏度) = raw * 0.01 - 273.15"
  - id: sipm_voltage1
    type: scaled_u2(1.25, 0.0)
    doc: "SiPM 通道1偏压; converted(mV) = raw * 1.25"
  - id: sipm_current1
    type: u2
    doc: SiPM 通道1电流（原始 uA）
  - id: sipm_temp1
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道1温度; converted(摄氏度) = raw * 0.01 - 273.15"
  - id: sipm_voltage2
    type: scaled_u2(1.25, 0.0)
    doc: "SiPM 通道2偏压; converted(mV) = raw * 1.25"
  - id: sipm_current2
    type: u2
    doc: SiPM 通道2电流（原始 uA）
  - id: sipm_temp2
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道2温度; converted(摄氏度) = raw * 0.01 - 273.15"
  - id: sipm_voltage3
    type: scaled_u2(1.25, 0.0)
    doc: "SiPM 通道3偏压; converted(mV) = raw * 1.25"
  - id: sipm_current3
    type: u2
    doc: SiPM 通道3电流（原始 uA）
  - id: sipm_temp3
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道3温度; converted(摄氏度) = raw * 0.01 - 273.15"
  # --- SAA / GPS / 姿态（178 版字段集）---
  - id: saa_judge_method
    type: u1
    enum: saa_judge_method
    doc: SAA 判定方式
  - id: reserved_105
    size: 1
    doc: 源 XML 未列出的 1 字节（105）
  - id: gps_status
    type: u1
    doc: GPS 状态
  - id: reserved_107
    size: 1
    doc: 源 XML 未列出的 1 字节（107）
  - id: gps_utc_s
    type: u4
    doc: GPS UTC 秒
  - id: gps_utc_ms
    type: u2
    doc: GPS UTC 毫秒
  - id: reserved_114
    size: 2
    doc: 源 XML 未列出的 2 字节（114..116）
  - id: gps_orbit_x
    type: u4
    doc: GPS 轨道位置 X（原始数字量）
  - id: gps_orbit_y
    type: u4
    doc: GPS 轨道位置 Y（原始数字量）
  - id: gps_orbit_z
    type: u4
    doc: GPS 轨道位置 Z（原始数字量）
  - id: gps_orbit_vx
    type: u4
    doc: GPS 轨道速度 VX（原始数字量）
  - id: gps_orbit_vy
    type: u4
    doc: GPS 轨道速度 VY（原始数字量）
  - id: gps_orbit_vz
    type: u4
    doc: GPS 轨道速度 VZ（原始数字量）
  - id: attitude_utc_s
    type: u4
    doc: 姿态 UTC 秒
  - id: attitude_utc_ms
    type: u2
    doc: 姿态 UTC 毫秒
  - id: reserved_146
    size: 2
    doc: 源 XML 未列出的 2 字节（146..148）
  - id: attitude_roll
    type: u4
    doc: 姿态 横滚（原始数字量）
  - id: attitude_pitch
    type: u4
    doc: 姿态 俯仰（原始数字量）
  - id: attitude_yaw
    type: u4
    doc: 姿态 偏航（原始数字量）
  - id: attitude_roll_rate
    type: u4
    doc: 姿态 横滚角速度（原始数字量）
  - id: attitude_pitch_rate
    type: u4
    doc: 姿态 俯仰角速度（原始数字量）
  - id: attitude_yaw_rate
    type: u4
    doc: 姿态 偏航角速度（原始数字量）
  - id: reserved_172
    size: 4
    doc: 源 XML 未列出的 4 字节（172..176）
  - id: crc16
    type: u2
    doc: "CRC16；覆盖 [0,176)（原 XML 名 CRC, skip0=skip1=0）"
enums:
  saa_judge_method:
    0x00: saa_cmd_enable_switch
    0x01: recalc_enable_switch
    0x02: rate_enable_switch
    0x10: saa_cmd_disable_switch
    0x11: recalc_disable_switch
    0x12: rate_disable_switch
types:
  scaled_u2:
    doc: 带线性换算的无符号 2 字节原始值（模式见 ksy/grid1x/grid1x_hk_packet.ksy）
    params:
      - id: scale
        type: f8
      - id: offset
        type: f8
    seq:
      - id: raw
        type: u2
        doc: 原始值（未换算）
    instances:
      converted:
        value: raw * scale + offset
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
    value: 2
    doc: "CRC 字段起点距包尾的字节数"
  body_data:
    pos: 0
    type: u1
    repeat: expr
    repeat-expr: 176
    doc: CRC 覆盖区间 [0, 176) 的字节视图
