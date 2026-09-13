# -*- mode: yaml -*-
meta:
  id: grid1x_hk_packet
  title: GRID-1X HK (Housekeeping) Telemetry Packet
  application: GRID Payload Monitor
  file-extension: hk
  endian: be
  ks-version: "0.9"
doc: |
  GRID-1X 遥测 (HK) 数据包。

  来源: xml/grid_packet.xml 中的 <grid1x_hk_packet> 定义
  - 包总长: 187 字节
  - 帧头: 0x1A 0x2B 0x3C 0x4D
  - 字节序: 大端 (MSB)
  - 包尾: CRC16 校验（字段 crc，计算时跳过首尾字节 skip0=0 skip1=0）

  命名说明：原 XML 中三个字段名含大写字母 A（fee_z5vA_*、fee_5vA_*），
  因 Kaitai 标识符规范要求全小写，转写时已改为小写 a。
seq:
  - id: header
    type: u4
    doc: 帧头 magic，固定值 0x1A2B3C4D（校验由应用层完成）
  - id: utc_time
    type: u4
    doc: UTC 时间戳（秒）
  - id: cpu_temperature
    type: u2
    doc: CPU 温度
  - id: daq_temperature_i2c1_0x49
    type: u2
    doc: DAQ 温度（I2C1，器件地址 0x49）
  - id: storage_valid
    type: u2
    doc: 存储有效标志
  # --- FEE 电源监测（电压/电流） ---
  - id: fee_z5v_v_0x40_1
    type: u2
    doc: FEE +5V 电压（0x40）
  - id: fee_z5v_i_0x40_1
    type: u2
    doc: FEE +5V 电流（0x40）
  - id: fee_z2v1_v_0x41_1
    type: u2
    doc: FEE +2.1V 电压（0x41）
  - id: fee_z2v1_i_0x41_1
    type: u2
    doc: FEE +2.1V 电流（0x41）
  - id: fee_z5v4_v_0x42_1
    type: u2
    doc: FEE +5.4V 电压（0x42）
  - id: fee_z5v4_i_0x42_1
    type: u2
    doc: FEE +5.4V 电流（0x42）
  - id: fee_z5va_v_0x4d_1
    type: u2
    doc: FEE +5VA 电压（0x4D）（原 XML 名为 fee_z5vA_v_0x4d_1）
  - id: fee_z5va_i_0x4d_1
    type: u2
    doc: FEE +5VA 电流（0x4D）（原 XML 名为 fee_z5vA_i_0x4d_1）
  - id: fee_5va_v_0x40
    type: u2
    doc: FEE 5VA 电压（0x40）（原 XML 名为 fee_5vA_v_0x40）
  - id: fee_5va_i_0x40
    type: u2
    doc: FEE 5VA 电流（0x40）（原 XML 名为 fee_5vA_i_0x40）
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
  # --- DAQ 电源监测（电压/电流） ---
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
    doc: DAQ +1.5V 电压（0x48）
  - id: daq_1v5_i_0x48_1
    type: u2
    doc: DAQ +1.5V 电流（0x48）
  # --- SiPM 通道 0-3（电压/电流/温度） ---
  - id: sipm_voltage0
    type: u2
    doc: SiPM 通道 0 偏压
  - id: sipm_current0
    type: u2
    doc: SiPM 通道 0 电流
  - id: sipm_temp0
    type: u2
    doc: SiPM 通道 0 温度
  - id: sipm_voltage1
    type: u2
    doc: SiPM 通道 1 偏压
  - id: sipm_current1
    type: u2
    doc: SiPM 通道 1 电流
  - id: sipm_temp1
    type: u2
    doc: SiPM 通道 1 温度
  - id: sipm_voltage2
    type: u2
    doc: SiPM 通道 2 偏压
  - id: sipm_current2
    type: u2
    doc: SiPM 通道 2 电流
  - id: sipm_temp2
    type: u2
    doc: SiPM 通道 2 温度
  - id: sipm_voltage3
    type: u2
    doc: SiPM 通道 3 偏压
  - id: sipm_current3
    type: u2
    doc: SiPM 通道 3 电流
  - id: sipm_temp3
    type: u2
    doc: SiPM 通道 3 温度
  # --- SAA 判定 ---
  - id: saa_judge_method
    type: u1
    doc: SAA 判定方式
  # --- GPS / WGS-84 ---
  - id: gps_seconds
    type: u4
    doc: GPS 秒计数
  - id: wgs_84_pos_x
    type: u4
    doc: WGS-84 位置 X
  - id: wgs_84_pos_y
    type: u4
    doc: WGS-84 位置 Y
  - id: wgs_84_pos_z
    type: u4
    doc: WGS-84 位置 Z
  - id: wgs_84_speed_x
    type: u4
    doc: WGS-84 速度 X
  - id: wgs_84_speed_y
    type: u4
    doc: WGS-84 速度 Y
  - id: wgs_84_speed_z
    type: u4
    doc: WGS-84 速度 Z
  # --- 星敏 1 ---
  - id: xingmin1_valid
    type: u1
    doc: 星敏 1 有效标志
  - id: xingmin1_seconds
    type: u4
    doc: 星敏 1 秒计数
  - id: xingmin1_mseconds
    type: u2
    doc: 星敏 1 毫秒计数
  - id: xingmin1_q0
    type: u4
    doc: 星敏 1 四元数 q0
  - id: xingmin1_q1
    type: u4
    doc: 星敏 1 四元数 q1
  - id: xingmin1_q2
    type: u4
    doc: 星敏 1 四元数 q2
  - id: xingmin1_q3
    type: u4
    doc: 星敏 1 四元数 q3
  # --- 星敏 2 ---
  - id: xingmin2_valid
    type: u1
    doc: 星敏 2 有效标志
  - id: xingmin2_seconds
    type: u4
    doc: 星敏 2 秒计数
  - id: xingmin2_mseconds
    type: u2
    doc: 星敏 2 毫秒计数
  - id: xingmin2_q0
    type: u4
    doc: 星敏 2 四元数 q0
  - id: xingmin2_q1
    type: u4
    doc: 星敏 2 四元数 q1
  - id: xingmin2_q2
    type: u4
    doc: 星敏 2 四元数 q2
  - id: xingmin2_q3
    type: u4
    doc: 星敏 2 四元数 q3
  # --- 经纬度 ---
  - id: longitude
    type: u2
    doc: 经度
  - id: latitude
    type: u2
    doc: 纬度
  # --- CRC16 校验 ---
  - id: crc
    type: u2
    doc: CRC16 校验（原 XML 名为 CRC，计算时跳过首尾字节 skip0=0 skip1=0）
