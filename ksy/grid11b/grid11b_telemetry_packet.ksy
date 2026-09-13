# -*- mode: yaml -*-
meta:
  id: grid11b_telemetry_packet
  title: GRID-11B 遥测数据包（96B，HEAD/TAIL 封装版）
  application: GRID Payload Monitor
  file-extension: tlm
  endian: be
  ks-version: "0.9"
doc: |
  GRID-11B 遥测数据包（来源: xml/grid_packet.xml 的 <grid11b_telemetry_packet>）。

  ## 布局（定长 96 字节）
    0..4     header = "HEAD" (0x48454144)
    4..70    遥测字段（66 字节）
    70..92   reserve（22 字节）
    92..96   tail = "TAIL" (0x5441494C)
    → 载荷 = 88 字节 = 4(HEAD) + 66 + 22 - 4 = 88 ✓

  ## 版本说明（重要：与 10b 版是"同一份 88B 载荷的两种封装"）
    | | 本文件（11B / grid_packet.xml） | `ksy/grid10b/grid10b_tel_packet.ksy`（10b / 《使用说明》V1.1） |
    |---|---|---|
    | 帧封装 | 4B "HEAD" + 4B "TAIL"，96B/帧 | 无魔数，88B/帧（CAN 拆分传输） |
    | 载荷对齐 | payload[i] ↔ 10b 的 frame[i]（整体 +4 偏移） | 同左 |
    | 尾部 2 字节 | 计入 `reserve`（22B） | 命名为 `sipm_hot_flag` + `heat_protect_threshold`（+ reserve 20B） |
    | latest_complete_cmd_arg | u1 × 4（4 个字节） | u4（1 个 32 位整数，字节序相同） |
    | cpu/daq 温度 | u1（本文件按 11B 标准，保留无符号） | s1（《使用说明》记为有符号摄氏度） |
    | 单位换算 | 本文件按《使用说明》标注 converted（见下），raw 一律保留 | 同 |
    | 枚举 | 见 enums（值定义取自《使用说明》，两种封装共用） | 同 |

  ## ⚠ 换算与枚举的来源
    - 11B 标准（grid_packet.xml）**只给出原始数字量**；本文件中的 `scaled_u2` 换算与 `enums`
      取自《天格地面演示系统使用说明 V1.1》（即 10b 版同名字段），因为两者载荷逐字节相同。
      若 11B 有单独的换算/取值文档，以那份为准（raw 字段始终保留原值，不受影响）。
    - cpu/daq 温度在《使用说明》中为 s1（有符号）；本文件按 11B 标准保持 u1，
      若实测出现 >127 的温度值，请改用 s1（见 `grid10b_tel_packet.ksy`）。

  ## 校验（语义级）
    - 本包型**没有 CRC 字段**（两版 XML 都未定义）→ src/validator.py 会自动跳过（`checked` 不增加）。
    - `.tlm` 也不在任何 CRC 算法的 SUPPORT 列表里（conf.json 顶层 CRC_ALGO）。
seq:
  - id: header
    contents: [0x48, 0x45, 0x41, 0x44]
    doc: 帧头 "HEAD"（contents 强校验）
  - id: current_can_bus
    type: u1
    enum: can_bus
    doc: "当前所使用 CAN 总线: 00H=自主A; AAH=自主B; A0H=强制A; 0AH=强制B"
  - id: telemetry_count
    type: u1
    doc: 遥测指令累计计数
  - id: cmd_count
    type: u1
    doc: 收到的指令累计计数
  - id: latest_received_cmd
    type: u1
    doc: 最新收到的指令码
  - id: latest_received_cmd_progress
    type: u1
    doc: "最新收到的指令执行进度, 单位: %"
  - id: latest_complete_cmd
    type: u1
    doc: 最新完成的指令码
  - id: latest_complete_cmd_arg
    type: u1
    repeat: expr
    repeat-expr: 4
    doc: 最新完成的指令参数（11B 标准记为 4 个字节；10b 版读作一个 u4）
  - id: latest_complete_cmd_exit
    type: u1
    doc: 最新完成的指令退出值
  - id: utc_time
    type: u4
    doc: UTC 时间戳
  - id: cpu_temperature
    type: u1
    doc: "ECU CPU0 温度; 11B 标准为 u1（《使用说明》记为 s1 摄氏度）"
  - id: daq_temperature_i2c1_0x49
    type: u1
    doc: "ECU DAQ 板卡温度（I2C1 0x49）; 11B 标准为 u1（《使用说明》记为 s1 摄氏度）"
  - id: system_power
    type: scaled_u2(0.1, 0.0)
    doc: "系统功耗; raw 单位 0.1W, converted 单位 W（换算取自《使用说明》）"
  - id: system_input_voltage
    type: scaled_u2(0.01, 0.0)
    doc: "系统输入电压; raw 单位 0.01V, converted 单位 V（换算取自《使用说明》）"
  - id: file_upload_progress
    type: u1
    doc: "文件上注进度, 单位: %"
  - id: file_upload_check
    type: u1
    enum: file_upload_check
    doc: "文件上注校验结果: 1=正常, 0=异常"
  - id: normal_or_backup
    type: u1
    enum: normal_or_backup
    doc: "ECU 主备系统状态: 1=主 flash, 2=备 flash"
  - id: storage_avaliable
    type: u2
    doc: "ECU 剩余储存空间, 单位: MB（原 XML 拼写 storage_avaliable）"
  - id: pl_version
    type: u1
    doc: ECU PL 端固件版本号
  - id: app_version
    type: u1
    doc: ECU 应用程序版本号
  - id: log_index
    type: u1
    doc: 当前日志文件序号
  - id: sci_data_index
    type: u1
    doc: 当前科学数据文件序号
  - id: sample_mode
    type: u1
    enum: sample_mode
    doc: "当前采数模式（见 enums）"
  - id: data_transfer_package_count
    type: u1
    doc: 数传数据包发送个数
  - id: saa_status
    type: u1
    enum: saa_status
    doc: "SAA 区状态: 0x00=离开 SAA, 0x01=进入 SAA"
  - id: entered_saa_count
    type: u1
    doc: SAA 区进入次数计数
  # --- SiPM 4 通道 × 电压/电流/温度 ---
  - id: sipm_voltage_ch0
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道0电压; raw 单位 mV, converted 单位 V"
  - id: sipm_current_ch0
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道0电流; raw 单位 uA, converted 单位 mA"
  - id: sipm_temprature_ch0
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道0温度; raw 单位 10mK, converted 单位 摄氏度（原 XML 拼写 temprature）"
  - id: sipm_voltage_ch1
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道1电压; raw 单位 mV, converted 单位 V"
  - id: sipm_current_ch1
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道1电流; raw 单位 uA, converted 单位 mA"
  - id: sipm_temprature_ch1
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道1温度; raw 单位 10mK, converted 单位 摄氏度"
  - id: sipm_voltage_ch2
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道2电压; raw 单位 mV, converted 单位 V"
  - id: sipm_current_ch2
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道2电流; raw 单位 uA, converted 单位 mA"
  - id: sipm_temprature_ch2
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道2温度; raw 单位 10mK, converted 单位 摄氏度"
  - id: sipm_voltage_ch3
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道3电压; raw 单位 mV, converted 单位 V"
  - id: sipm_current_ch3
    type: scaled_u2(0.001, 0.0)
    doc: "SiPM 通道3电流; raw 单位 uA, converted 单位 mA"
  - id: sipm_temprature_ch3
    type: scaled_u2(0.01, -273.15)
    doc: "SiPM 通道3温度; raw 单位 10mK, converted 单位 摄氏度"
  - id: count_rate0
    type: u2
    doc: "探测器0计数率, 单位: cps"
  - id: count_rate1
    type: u2
    doc: "探测器1计数率, 单位: cps"
  - id: count_rate2
    type: u2
    doc: "探测器2计数率, 单位: cps"
  - id: count_rate3
    type: u2
    doc: "探测器3计数率, 单位: cps"
  - id: reserve
    type: u1
    repeat: expr
    repeat-expr: 22
    doc: "保留字段（22 字节）。⚠ 10b 版把其中前 2 字节命名为 sipm_hot_flag + heat_protect_threshold"
  - id: tail
    contents: [0x54, 0x41, 0x49, 0x4c]
    doc: 帧尾 "TAIL"（contents 强校验）
enums:
  can_bus:
    0x00: auto_a_bus
    0xaa: auto_b_bus
    0xa0: force_a_bus
    0x0a: force_b_bus
  file_upload_check:
    0: error
    1: normal
  normal_or_backup:
    1: master_flash
    2: backup_flash
  sample_mode:
    2: event_feature
    3: event_waveform
    4: energy_feature
    5: energy_waveform
    6: event_energy_feature
    7: event_energy_waveform
  saa_status:
    0x00: left_saa
    0x01: in_saa
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
