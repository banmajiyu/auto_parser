meta:
  id: grid1x_hk_packet
  endian: be
  file-extension: hk
doc: |
  天格 grid1x HK（Housekeeping）数据包 —— 187 字节标准。
  来源: xml/grid_packet.xml 的 <grid1x_hk_packet>。

  ## 版本与用法（务必区分）
    - 本文件 = **1x 版**：命名沿用 10b、但换算**只按 XML tag 给出**（仅 SiPM 三处），
      其余字段保留原始数字量（u2/u4，不用 s2/s4）。
    - 10b 版（同 187B 布局，《使用说明》V1.1 的全套换算 + s2/s4）见 `ksy/grid10b/grid10b_hk_packet.ksy`；
      178B 精简版（yingtian，字段集不同）见 `ksy/grid1x/grid1x_hk_packet_178.ksy`。
    - pipeline 用法：conf.json 注册 `PACKET_LEN = 187`；本文件是"单包"写法（非 frameseq）。

  - 帧长 187 字节 = 帧头(4) + 遥测字段(181) + CRC16(2)
  - 帧头 0x1A2B3C4D 用 contents 声明，由 Kaitai 逐字节强校验
  - 字节序: 大端 (be)
  - CRC16 覆盖 [header, crc16) 区间（原 XML 名 CRC, skip0=skip1=0），
    由 src/validator.py 按解析参数校验（ksy 不含校验信息）
  - 字段命名沿用 grid10b_hk.ksy；与 XML 原名的对应关系（如
    fee_z5v_v_0x40_1 -> voltage_i2c1_0x40、sipm_voltage0 -> voltage_sipm_ch0、
    xingmin1_mseconds -> xingmin1_microseconds、CRC -> crc16）见本目录文件
    `ksy/grid1x/grid1x_hk_packet.ksy` 的 doc 与 `ksy/grid10b/housekeepping_data_format.md`。

  换算规则（按本标准给出的 tag 定义；未列出的字段无换算，保留原始数字量）:
  - sipm_voltage: converted(mV)     = raw * 1.25
  - sipm_current: 无换算，raw 单位 uA
  - sipm_temp:    converted(摄氏度) = raw * 0.01 - 273.15
  - ADC 电源监测（fee_*/daq_*）、GPS/WGS-84、星敏、星下点经纬度: 原始数字量
seq:
  - id: header
    contents: [0x1A, 0x2B, 0x3C, 0x4D]
    doc: 帧头 magic, 固定 0x1A2B3C4D（contents 强校验；原 XML 名 head）
  - id: utc_time
    type: u4
    doc: UTC 时间戳
  - id: cpu_temperature
    type: u2
    doc: CPU 温度数字量
  - id: daq_temperature_i2c1_0x49
    type: u2
    doc: DAQ 温度数字量（I2C1 器件地址 0x49）
  - id: storage_valid
    type: u2
    doc: "ECU 剩余存储空间, 单位: 1MB"
  # --- FEE 转接板电源监测（I2C1）---
  - id: voltage_i2c1_0x40
    type: u2
    doc: "FEE 转接板 5V 电路电压 (I2C1 0x40); 原始 ADC 数字量"
  - id: current_i2c1_0x40
    type: u2
    doc: "FEE 转接板 5V 电路电流 (I2C1 0x40); 原始 ADC 数字量"
  - id: voltage_i2c1_0x41
    type: u2
    doc: "FEE 转接板 2.1V 电路电压 (I2C1 0x41); 原始 ADC 数字量"
  - id: current_i2c1_0x41
    type: u2
    doc: "FEE 转接板 2.1V 电路电流 (I2C1 0x41); 原始 ADC 数字量"
  - id: voltage_i2c1_0x42
    type: u2
    doc: "FEE 转接板 5.4V 电路电压 (I2C1 0x42); 原始 ADC 数字量"
  - id: current_i2c1_0x42
    type: u2
    doc: "FEE 转接板 5.4V 电路电流 (I2C1 0x42); 原始 ADC 数字量"
  - id: voltage_i2c1_0x4d
    type: u2
    doc: "FEE 转接板 5VA 电路电压 (I2C1 0x4D); 原始 ADC 数字量"
  - id: current_i2c1_0x4d
    type: u2
    doc: "FEE 转接板 5VA 电路电流 (I2C1 0x4D); 原始 ADC 数字量"
  # --- FEE 电源监测（I2C2）---
  - id: voltage_i2c2_0x40
    type: u2
    doc: "FEE 5VA 电路电压 (I2C2 0x40); 原始 ADC 数字量"
  - id: current_i2c2_0x40
    type: u2
    doc: "FEE 5VA 电路电流 (I2C2 0x40); 原始 ADC 数字量"
  - id: voltage_i2c2_0x41
    type: u2
    doc: "FEE 1.8VA 电路电压 (I2C2 0x41); 原始 ADC 数字量"
  - id: current_i2c2_0x41
    type: u2
    doc: "FEE 1.8VA 电路电流 (I2C2 0x41); 原始 ADC 数字量"
  - id: voltage_i2c2_0x42
    type: u2
    doc: "FEE 3V3 电路电压 (I2C2 0x42); 原始 ADC 数字量"
  - id: current_i2c2_0x42
    type: u2
    doc: "FEE 3V3 电路电流 (I2C2 0x42); 原始 ADC 数字量"
  - id: voltage_i2c2_0x43
    type: u2
    doc: "FEE 1.8VD 电路电压 (I2C2 0x43); 原始 ADC 数字量"
  - id: current_i2c2_0x43
    type: u2
    doc: "FEE 1.8VD 电路电流 (I2C2 0x43); 原始 ADC 数字量"
  - id: voltage_i2c2_0x44
    type: u2
    doc: "FEE P5VA_1 电路电压 (I2C2 0x44); 原始 ADC 数字量"
  - id: current_i2c2_0x44
    type: u2
    doc: "FEE P5VA_1 电路电流 (I2C2 0x44); 原始 ADC 数字量"
  - id: voltage_i2c2_0x45
    type: u2
    doc: "FEE P5VA_2 电路电压 (I2C2 0x45); 原始 ADC 数字量"
  - id: current_i2c2_0x45
    type: u2
    doc: "FEE P5VA_2 电路电流 (I2C2 0x45); 原始 ADC 数字量"
  - id: voltage_i2c2_0x46
    type: u2
    doc: "FEE P5VA_3 电路电压 (I2C2 0x46); 原始 ADC 数字量"
  - id: current_i2c2_0x46
    type: u2
    doc: "FEE P5VA_3 电路电流 (I2C2 0x46); 原始 ADC 数字量"
  - id: voltage_i2c2_0x47
    type: u2
    doc: "FEE P5VA_4 电路电压 (I2C2 0x47); 原始 ADC 数字量"
  - id: current_i2c2_0x47
    type: u2
    doc: "FEE P5VA_4 电路电流 (I2C2 0x47); 原始 ADC 数字量"
  # --- DAQ 电源监测（I2C1）---
  - id: voltage_i2c1_0x43
    type: u2
    doc: "DAQ 1V0 电路电压 (I2C1 0x43); 原始 ADC 数字量"
  - id: current_i2c1_0x43
    type: u2
    doc: "DAQ 1V0 电路电流 (I2C1 0x43); 原始 ADC 数字量"
  - id: voltage_i2c1_0x44
    type: u2
    doc: "DAQ 1V8 电路电压 (I2C1 0x44); 原始 ADC 数字量"
  - id: current_i2c1_0x44
    type: u2
    doc: "DAQ 1V8 电路电流 (I2C1 0x44); 原始 ADC 数字量"
  - id: voltage_i2c1_0x45
    type: u2
    doc: "DAQ 2V5 电路电压 (I2C1 0x45, 实测 DCDC 前置约 5V); 原始 ADC 数字量"
  - id: current_i2c1_0x45
    type: u2
    doc: "DAQ 2V5 电路电流 (I2C1 0x45); 原始 ADC 数字量"
  - id: voltage_i2c1_0x47
    type: u2
    doc: "DAQ 3V3 电路电压 (I2C1 0x47); 原始 ADC 数字量"
  - id: current_i2c1_0x47
    type: u2
    doc: "DAQ 3V3 电路电流 (I2C1 0x47); 原始 ADC 数字量"
  - id: voltage_i2c1_0x48
    type: u2
    doc: "DAQ 1V5 电路电压 (I2C1 0x48); 原始 ADC 数字量"
  - id: current_i2c1_0x48
    type: u2
    doc: "DAQ 1V5 电路电流 (I2C1 0x48); 原始 ADC 数字量"
  # --- SiPM 通道 0-3（电压/电流/温度）---
  - id: voltage_sipm_ch0
    type: scaled_u2(1.25, 0.0)
    doc: "SiPM 通道0电压; converted(mV) = raw * 1.25"
  - id: current_sipm_ch0
    type: u2
    doc: "SiPM 通道0电流; 单位 uA（无换算）"
  - id: temperature_sipm_ch0
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道0温度; converted(摄氏度) = raw * 0.01 - 273.15"
  - id: voltage_sipm_ch1
    type: scaled_u2(1.25, 0.0)
    doc: "SiPM 通道1电压; converted(mV) = raw * 1.25"
  - id: current_sipm_ch1
    type: u2
    doc: "SiPM 通道1电流; 单位 uA（无换算）"
  - id: temperature_sipm_ch1
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道1温度; converted(摄氏度) = raw * 0.01 - 273.15"
  - id: voltage_sipm_ch2
    type: scaled_u2(1.25, 0.0)
    doc: "SiPM 通道2电压; converted(mV) = raw * 1.25"
  - id: current_sipm_ch2
    type: u2
    doc: "SiPM 通道2电流; 单位 uA（无换算）"
  - id: temperature_sipm_ch2
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道2温度; converted(摄氏度) = raw * 0.01 - 273.15"
  - id: voltage_sipm_ch3
    type: scaled_u2(1.25, 0.0)
    doc: "SiPM 通道3电压; converted(mV) = raw * 1.25"
  - id: current_sipm_ch3
    type: u2
    doc: "SiPM 通道3电流; 单位 uA（无换算）"
  - id: temperature_sipm_ch3
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道3温度; converted(摄氏度) = raw * 0.01 - 273.15"
  # --- SAA 区判定方式 ---
  - id: saa_judge_method
    type: u1
    enum: saa_judge_method
    doc: "SAA 区判定方式; 低 4 位为判定方式, bit4 表示进出 SAA 区是否切换观测模式(1=不切换, 0=切换)"
  # --- GPS 广播 ---
  - id: gps_seconds
    type: u4
    doc: "GPS 广播 UTC 累计秒; 基准时间 2000-01-01 12:00:00（原始值）"
  - id: wgs_84_pos_x
    type: u4
    doc: "GPS 广播 WGS-84 位置 X; 原始数字量（本标准未定义换算）"
  - id: wgs_84_pos_y
    type: u4
    doc: "GPS 广播 WGS-84 位置 Y; 原始数字量（本标准未定义换算）"
  - id: wgs_84_pos_z
    type: u4
    doc: "GPS 广播 WGS-84 位置 Z; 原始数字量（本标准未定义换算）"
  - id: wgs_84_speed_x
    type: u4
    doc: "GPS 广播 WGS-84 速度 X; 原始数字量（本标准未定义换算）"
  - id: wgs_84_speed_y
    type: u4
    doc: "GPS 广播 WGS-84 速度 Y; 原始数字量（本标准未定义换算）"
  - id: wgs_84_speed_z
    type: u4
    doc: "GPS 广播 WGS-84 速度 Z; 原始数字量（本标准未定义换算）"
  # --- 星敏 1 ---
  - id: xingmin1_valid
    type: u1
    enum: valid_flag
    doc: 星敏1 数据有效性标识（1=有效, 0=无效）
  - id: xingmin1_seconds
    type: u4
    doc: "星敏1 UTC 累计秒; 基准时间 2000-01-01 12:00:00（原始值）"
  - id: xingmin1_microseconds
    type: u2
    doc: 星敏1 曝光时差（原 XML 名 xingmin1_mseconds）
  - id: xingmin1_q0
    type: u4
    doc: 星敏1 四元数 q0（矢量, 原始数字量）
  - id: xingmin1_q1
    type: u4
    doc: 星敏1 四元数 q1（矢量, 原始数字量）
  - id: xingmin1_q2
    type: u4
    doc: 星敏1 四元数 q2（矢量, 原始数字量）
  - id: xingmin1_q3
    type: u4
    doc: 星敏1 四元数 q3（标量, 原始数字量）
  # --- 星敏 2 ---
  - id: xingmin2_valid
    type: u1
    enum: valid_flag
    doc: 星敏2 数据有效性标识（1=有效, 0=无效）
  - id: xingmin2_seconds
    type: u4
    doc: "星敏2 UTC 累计秒; 基准时间 2000-01-01 12:00:00（原始值）"
  - id: xingmin2_microseconds
    type: u2
    doc: 星敏2 曝光时差（原 XML 名 xingmin2_mseconds）
  - id: xingmin2_q0
    type: u4
    doc: 星敏2 四元数 q0（矢量, 原始数字量）
  - id: xingmin2_q1
    type: u4
    doc: 星敏2 四元数 q1（矢量, 原始数字量）
  - id: xingmin2_q2
    type: u4
    doc: 星敏2 四元数 q2（矢量, 原始数字量）
  - id: xingmin2_q3
    type: u4
    doc: 星敏2 四元数 q3（标量, 原始数字量）
  # --- 星下点经纬度 ---
  - id: longitude
    type: u2
    doc: 星下点经度（原始数字量, 本标准未定义换算）
  - id: latitude
    type: u2
    doc: 星下点纬度（原始数字量, 本标准未定义换算）
  # --- CRC16 ---
  - id: crc16
    type: u2
    doc: "CRC16; 覆盖 [header, crc16) 区间, 由 src/validator.py 自动校验（原 XML 名 CRC, skip0=skip1=0）"
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
    doc: 带线性换算的无符号 2 字节原始值（模式参考 tel.ksy / grid10b_hk.ksy 的 scaled）
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

