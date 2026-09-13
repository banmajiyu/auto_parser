meta:
  id: grid10b_hk_packet
  endian: be
  file-extension: hk
doc: |
  天格 grid10b hk 内务（Housekeeping）数据包，根据《星测未来——天格地面演示系统使 用说明-V1.1》编写。

  ## 版本与用法（务必区分）
    - 本文件 = **10b 版**（《使用说明》V1.1）：187 字节/帧，ADC/SiPM/GPS 等使用《使用说明》的
      全套换算，ADC 用 s2、GPS/四元数用 s4（换算是**本版标准给出的**）。
    - 1x 版（同样 187B 布局，但只做 XML tag 的换算、其余保留原始数字量）见
      `ksy/grid1x/grid1x_hk_packet.ksy`；178B 精简版（字段集不同）见 `ksy/grid1x/grid1x_hk_packet_178.ksy`。
    - pipeline 用法：conf.json 注册 `PACKET_LEN = 187`；本文件是"单包"写法（非 frameseq）。

  - 帧长 187 字节 = 帧头(4) + 遥测字段(181) + CRC16(2)
  - 帧头 0x1A2B3C4D 用 contents 声明，由 Kaitai 逐字节强校验
  - 字节序: 大端 (be)
  - CRC16 覆盖 [header, crc16) 区间，由 src/validator.py 按解析参数校验（ksy 不含校验信息）
  - 单位换算沿用 tel.ksy 的 scaled 参数化类型: raw 为协议原始数字量, converted 为工程值

  换算约定:
  - 电压(V)           = 数字量 * 1.25mV
  - 电流(mA)          = 数字量 * 2.5uV / R * 1000（R = 该路采样电阻, 见各字段 doc）
  - SiPM 温度(摄氏度)  = 数字量 / 100 - 273.15
  - 星敏四元数         = 数字量 / 2147483647
  - WGS-84 位置(m)/速度(m/s): 权重 0.01
  - 星下点经/纬度(度): 权重 0.01
seq:
  - id: header
    contents: [0x1A, 0x2B, 0x3C, 0x4D]
    doc: 帧头 magic, 固定 0x1A2B3C4D（contents 强校验）
  - id: utc_time
    type: u4
    doc: UTC 时间戳
  - id: cpu_temperature
    type: u2
    doc: CPU 温度数字量（参考温度计算方法）
  - id: daq_temperature_i2c1_0x49
    type: u2
    doc: DAQ 温度数字量（I2C1 器件地址 0x49，参考温度计算方法）
  - id: storage_valid
    type: u2
    doc: "ECU 剩余存储空间, 单位: 1MB"
  # --- FEE 转接板电源监测（I2C1）---
  - id: voltage_i2c1_0x40
    type: scaled_s2(0.00125, 0.0)
    doc: "FEE 转接板 5V 电路电压 (I2C1 0x40); converted 单位 V"
  - id: current_i2c1_0x40
    type: scaled_s2(2.5 / 1000 / 0.02, 0.0)
    doc: "FEE 转接板 5V 电路电流 (I2C1 0x40); R=0.02Ω, converted 单位 mA"
  - id: voltage_i2c1_0x41
    type: scaled_s2(0.00125, 0.0)
    doc: "FEE 转接板 2.1V 电路电压 (I2C1 0x41); converted 单位 V"
  - id: current_i2c1_0x41
    type: scaled_s2(2.5 / 1000 / 0.12, 0.0)
    doc: "FEE 转接板 2.1V 电路电流 (I2C1 0x41); R=0.12Ω, converted 单位 mA"
  - id: voltage_i2c1_0x42
    type: scaled_s2(0.00125, 0.0)
    doc: "FEE 转接板 5.4V 电路电压 (I2C1 0x42); converted 单位 V"
  - id: current_i2c1_0x42
    type: scaled_s2(2.5 / 1000 / 0.12, 0.0)
    doc: "FEE 转接板 5.4V 电路电流 (I2C1 0x42); R=0.12Ω, converted 单位 mA"
  - id: voltage_i2c1_0x4d
    type: scaled_s2(0.00125, 0.0)
    doc: "FEE 转接板 5VA 电路电压 (I2C1 0x4D); converted 单位 V"
  - id: current_i2c1_0x4d
    type: scaled_s2(2.5 / 1000 / 0.12, 0.0)
    doc: "FEE 转接板 5VA 电路电流 (I2C1 0x4D); R=0.12Ω, converted 单位 mA"
  # --- FEE 电源监测（I2C2）---
  - id: voltage_i2c2_0x40
    type: scaled_s2(0.00125, 0.0)
    doc: "FEE 5VA 电路电压 (I2C2 0x40); converted 单位 V"
  - id: current_i2c2_0x40
    type: scaled_s2(2.5 / 1000 / 0.06, 0.0)
    doc: "FEE 5VA 电路电流 (I2C2 0x40); R=0.06Ω, converted 单位 mA"
  - id: voltage_i2c2_0x41
    type: scaled_s2(0.00125, 0.0)
    doc: "FEE 1.8VA 电路电压 (I2C2 0x41); converted 单位 V"
  - id: current_i2c2_0x41
    type: scaled_s2(2.5 / 1000 / 0.06, 0.0)
    doc: "FEE 1.8VA 电路电流 (I2C2 0x41); R=0.06Ω, converted 单位 mA"
  - id: voltage_i2c2_0x42
    type: scaled_s2(0.00125, 0.0)
    doc: "FEE 3V3 电路电压 (I2C2 0x42); converted 单位 V"
  - id: current_i2c2_0x42
    type: scaled_s2(2.5 / 1000 / 0.06, 0.0)
    doc: "FEE 3V3 电路电流 (I2C2 0x42); R=0.06Ω, converted 单位 mA"
  - id: voltage_i2c2_0x43
    type: scaled_s2(0.00125, 0.0)
    doc: "FEE 1.8VD 电路电压 (I2C2 0x43); converted 单位 V"
  - id: current_i2c2_0x43
    type: scaled_s2(2.5 / 1000 / 0.06, 0.0)
    doc: "FEE 1.8VD 电路电流 (I2C2 0x43); R=0.06Ω, converted 单位 mA"
  - id: voltage_i2c2_0x44
    type: scaled_s2(0.00125, 0.0)
    doc: "FEE P5VA_1 电路电压 (I2C2 0x44); converted 单位 V"
  - id: current_i2c2_0x44
    type: scaled_s2(2.5 / 1000 / 0.06, 0.0)
    doc: "FEE P5VA_1 电路电流 (I2C2 0x44); R=0.06Ω, converted 单位 mA"
  - id: voltage_i2c2_0x45
    type: scaled_s2(0.00125, 0.0)
    doc: "FEE P5VA_2 电路电压 (I2C2 0x45); converted 单位 V"
  - id: current_i2c2_0x45
    type: scaled_s2(2.5 / 1000 / 0.06, 0.0)
    doc: "FEE P5VA_2 电路电流 (I2C2 0x45); R=0.06Ω, converted 单位 mA"
  - id: voltage_i2c2_0x46
    type: scaled_s2(0.00125, 0.0)
    doc: "FEE P5VA_3 电路电压 (I2C2 0x46); converted 单位 V"
  - id: current_i2c2_0x46
    type: scaled_s2(2.5 / 1000 / 0.06, 0.0)
    doc: "FEE P5VA_3 电路电流 (I2C2 0x46); R=0.06Ω, converted 单位 mA"
  - id: voltage_i2c2_0x47
    type: scaled_s2(0.00125, 0.0)
    doc: "FEE P5VA_4 电路电压 (I2C2 0x47); converted 单位 V"
  - id: current_i2c2_0x47
    type: scaled_s2(2.5 / 1000 / 0.06, 0.0)
    doc: "FEE P5VA_4 电路电流 (I2C2 0x47); R=0.06Ω, converted 单位 mA"
  # --- DAQ 电源监测（I2C1）---
  - id: voltage_i2c1_0x43
    type: scaled_s2(0.00125, 0.0)
    doc: "DAQ 1V0 电路电压 (I2C1 0x43); converted 单位 V"
  - id: current_i2c1_0x43
    type: scaled_s2(2.5 / 1000 / 0.03, 0.0)
    doc: "DAQ 1V0 电路电流 (I2C1 0x43); R=0.03Ω, converted 单位 mA"
  - id: voltage_i2c1_0x44
    type: scaled_s2(0.00125, 0.0)
    doc: "DAQ 1V8 电路电压 (I2C1 0x44); converted 单位 V"
  - id: current_i2c1_0x44
    type: scaled_s2(2.5 / 1000 / 0.03, 0.0)
    doc: "DAQ 1V8 电路电流 (I2C1 0x44); R=0.03Ω, converted 单位 mA"
  - id: voltage_i2c1_0x45
    type: scaled_s2(0.00125, 0.0)
    doc: "DAQ 2V5 电路电压 (I2C1 0x45, 实测 DCDC 前置约 5V); converted 单位 V"
  - id: current_i2c1_0x45
    type: scaled_s2(2.5 / 1000 / 0.04, 0.0)
    doc: "DAQ 2V5 电路电流 (I2C1 0x45); R=0.04Ω, converted 单位 mA"
  - id: voltage_i2c1_0x47
    type: scaled_s2(0.00125, 0.0)
    doc: "DAQ 3V3 电路电压 (I2C1 0x47); converted 单位 V"
  - id: current_i2c1_0x47
    type: scaled_s2(2.5 / 1000 / 0.03, 0.0)
    doc: "DAQ 3V3 电路电流 (I2C1 0x47); R=0.03Ω, converted 单位 mA"
  - id: voltage_i2c1_0x48
    type: scaled_s2(0.00125, 0.0)
    doc: "DAQ 1V5 电路电压 (I2C1 0x48); converted 单位 V"
  - id: current_i2c1_0x48
    type: scaled_s2(2.5 / 1000 / 0.075, 0.0)
    doc: "DAQ 1V5 电路电流 (I2C1 0x48); R=0.075Ω, converted 单位 mA"
  # --- SiPM 通道 0-3（电压/电流/温度）---
  - id: voltage_sipm_ch0
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道0电压; raw 单位 mV, converted 单位 V"
  - id: current_sipm_ch0
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道0电流; raw 单位 uA, converted 单位 mA"
  - id: temperature_sipm_ch0
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道0温度; Tc = raw / 100 - 273.15（摄氏度）"
  - id: voltage_sipm_ch1
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道1电压; raw 单位 mV, converted 单位 V"
  - id: current_sipm_ch1
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道1电流; raw 单位 uA, converted 单位 mA"
  - id: temperature_sipm_ch1
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道1温度; Tc = raw / 100 - 273.15（摄氏度）"
  - id: voltage_sipm_ch2
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道2电压; raw 单位 mV, converted 单位 V"
  - id: current_sipm_ch2
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道2电流; raw 单位 uA, converted 单位 mA"
  - id: temperature_sipm_ch2
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道2温度; Tc = raw / 100 - 273.15（摄氏度）"
  - id: voltage_sipm_ch3
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道3电压; raw 单位 mV, converted 单位 V"
  - id: current_sipm_ch3
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道3电流; raw 单位 uA, converted 单位 mA"
  - id: temperature_sipm_ch3
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道3温度; Tc = raw / 100 - 273.15（摄氏度）"
  # --- SAA 区判定方式 ---
  - id: saa_judge_method
    type: u1
    enum: saa_judge_method
    doc: "SAA 区判定方式; 低 4 位为判定方式, bit4 表示进出 SAA 区是否切换观测模式(1=不切换, 0=切换)"
  # --- GPS 广播 ---
  - id: gps_seconds
    type: u4
    doc: "GPS 广播 UTC 累计秒; 基准时间 2000-01-01 12:00:00"
  - id: wgs_84_pos_x
    type: scaled_s4(0.01, 0.0)
    doc: "GPS 广播 WGS-84 位置 X; raw 权重 0.01m/bit, converted 单位 m"
  - id: wgs_84_pos_y
    type: scaled_s4(0.01, 0.0)
    doc: "GPS 广播 WGS-84 位置 Y; raw 权重 0.01m/bit, converted 单位 m"
  - id: wgs_84_pos_z
    type: scaled_s4(0.01, 0.0)
    doc: "GPS 广播 WGS-84 位置 Z; raw 权重 0.01m/bit, converted 单位 m"
  - id: wgs_84_speed_x
    type: scaled_s4(0.01, 0.0)
    doc: "GPS 广播 WGS-84 速度 X; raw 权重 0.01(m/s)/bit, converted 单位 m/s"
  - id: wgs_84_speed_y
    type: scaled_s4(0.01, 0.0)
    doc: "GPS 广播 WGS-84 速度 Y; raw 权重 0.01(m/s)/bit, converted 单位 m/s"
  - id: wgs_84_speed_z
    type: scaled_s4(0.01, 0.0)
    doc: "GPS 广播 WGS-84 速度 Z; raw 权重 0.01(m/s)/bit, converted 单位 m/s"
  # --- 星敏 1 ---
  - id: xingmin1_valid
    type: u1
    enum: valid_flag
    doc: 星敏1 数据有效性标识（1=有效, 0=无效）
  - id: xingmin1_seconds
    type: u4
    doc: "星敏1 UTC 累计秒; 基准时间 2000-01-01 12:00:00"
  - id: xingmin1_microseconds
    type: s2
    doc: 星敏1 曝光时差
  - id: xingmin1_q0
    type: scaled_s4(1.0 / 2147483647.0, 0.0)
    doc: "星敏1 四元数 q0（矢量, 星敏坐标系相对 J2000）; converted 为归一化值"
  - id: xingmin1_q1
    type: scaled_s4(1.0 / 2147483647.0, 0.0)
    doc: "星敏1 四元数 q1（矢量, 星敏坐标系相对 J2000）; converted 为归一化值"
  - id: xingmin1_q2
    type: scaled_s4(1.0 / 2147483647.0, 0.0)
    doc: "星敏1 四元数 q2（矢量, 星敏坐标系相对 J2000）; converted 为归一化值"
  - id: xingmin1_q3
    type: scaled_s4(1.0 / 2147483647.0, 0.0)
    doc: "星敏1 四元数 q3（标量, 星敏坐标系相对 J2000）; converted 为归一化值"
  # --- 星敏 2 ---
  - id: xingmin2_valid
    type: u1
    enum: valid_flag
    doc: 星敏2 数据有效性标识（1=有效, 0=无效）
  - id: xingmin2_seconds
    type: u4
    doc: "星敏2 UTC 累计秒; 基准时间 2000-01-01 12:00:00"
  - id: xingmin2_microseconds
    type: s2
    doc: 星敏2 曝光时差
  - id: xingmin2_q0
    type: scaled_s4(1.0 / 2147483647.0, 0.0)
    doc: "星敏2 四元数 q0（矢量, 星敏坐标系相对 J2000）; converted 为归一化值"
  - id: xingmin2_q1
    type: scaled_s4(1.0 / 2147483647.0, 0.0)
    doc: "星敏2 四元数 q1（矢量, 星敏坐标系相对 J2000）; converted 为归一化值"
  - id: xingmin2_q2
    type: scaled_s4(1.0 / 2147483647.0, 0.0)
    doc: "星敏2 四元数 q2（矢量, 星敏坐标系相对 J2000）; converted 为归一化值"
  - id: xingmin2_q3
    type: scaled_s4(1.0 / 2147483647.0, 0.0)
    doc: "星敏2 四元数 q3（标量, 星敏坐标系相对 J2000）; converted 为归一化值"
  # --- 星下点经纬度 ---
  - id: longitude
    type: scaled_s2(0.01, 0.0)
    doc: "星下点经度; raw 权重 0.01度/bit, converted 单位 度"
  - id: latitude
    type: scaled_s2(0.01, 0.0)
    doc: "星下点纬度; raw 权重 0.01度/bit, converted 单位 度"
  # --- CRC16 ---
  - id: crc16
    type: u2
    doc: "CRC16; 覆盖 [header, crc16) 区间, 由 src/validator.py 自动校验"
instances:
  # --- CRC 校验元数据（供 src/validator.py 读取；声明后优先于 conf 的默认值）---
  crc_skip0:
    value: 0
    doc: "CRC 计算时从包首跳过的字节数（XML: skip0）"
  crc_skip1:
    value: 0
    doc: "CRC 计算时从结尾向前排除的字节数（XML: skip1）"
  crc_bytes:
    value: 2
    doc: "CRC 字段字节数（XML: byte）"
  crc_tail:
    value: 2
    doc: "CRC 字段起点距包尾的字节数（ksy 声明后优先于 conf 的 TAIL）"
  body_data:
    pos: 0
    type: u1
    repeat: expr
    repeat-expr: 185
enums:
  valid_flag:
    0: invalid
    1: valid
  saa_judge_method:
    0x00: saa_cmd_enable_switch
    0x01: recalc_enable_switch
    0x02: rate_enable_switch
    0x10: saa_cmd_disable_switch
    0x11: recalc_disable_switch
    0x12: rate_disable_switch

types:
  scaled_u2:
    doc: 带线性换算的无符号 2 字节原始值（模式参考 tel.ksy 的 scaled）
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
  scaled_s2:
    doc: 带线性换算的有符号 2 字节原始值
    params:
      - id: scale
        type: f8
      - id: offset
        type: f8
    seq:
      - id: raw
        type: s2
        doc: 原始值（未换算）
    instances:
      converted:
        value: raw * scale + offset
  scaled_s4:
    doc: 带线性换算的有符号 4 字节原始值
    params:
      - id: scale
        type: f8
      - id: offset
        type: f8
    seq:
      - id: raw
        type: s4
        doc: 原始值（未换算）
    instances:
      converted:
        value: raw * scale + offset

