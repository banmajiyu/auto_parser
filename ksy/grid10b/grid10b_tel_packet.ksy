meta:
  id: grid10b_tel_packet
  endian: be
  file-extension: tlm
doc: |
  天格 grid10b-tel 遥测数据包（《星测未来——天格地面演示系统使用说明 V1.1》，88 字节/帧）。

  ## 版本与用法（务必区分）
    - 本文件 = **10b 版**：88 字节/帧、**无帧头/帧尾魔数**（原始 CAN 拆分载荷）。
    - 11B 版（96 字节 = 4B "HEAD" + 88B 载荷 + 4B "TAIL"）见
      `ksy/grid11b/grid11b_telemetry_packet.ksy`；两版**载荷逐字节相同**
      （本文件 frame[i] ↔ 11B payload[i]，见该文件 doc 的对照表）。
    - 尾部 2 字节：本文件命名为 `sipm_hot_flag` + `heat_protect_threshold`（+ reserve 20）；
      11B 标准把这 2 字节并入 `reserve(22)`。
    - 本文件保留《使用说明》的换算（scaled）与枚举；11B 标准本身只给原始数字量。
    - pipeline 用法：conf.json 注册 `PACKET_LEN = 88`；本文件是"单包"写法（非 frameseq）。
seq:
  - id: current_can_bus
    type: u1
    doc: "当前所使用 CAN 总线: 00H = 自主A总线; AAH = 自主B总线; A0H = 强制A总线; 0AH = 强制B总线"
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
    doc: 最新收到的指令执行进度，单位：%
  - id: latest_complete_cmd
    type: u1
    doc: 最新完成的指令码
  - id: latest_complete_cmd_arg
    type: u4
    doc: 最新完成的指令参数
  - id: latest_complete_cmd_exit
    type: u1
    doc: 最新完成的指令退出值
  - id: utc_time
    type: u4
    doc: UTC 时间戳
  - id: ecu_cpu_tempratrue
    type: s1
    doc: "ECU CPU0温度, 单位: 摄氏度"
  - id: daq_temperature_i2c1_0x49
    type: s1
    doc: "ECU DAQ 板卡温度, 单位: 摄氏度"
  - id: system_power
    type: scaled(0.1, 0.0)
    doc: "系统功耗, 原始单位 0.1W（converted 单位: W）"
  - id: system_input_voltage
    type: scaled(0.01, 0.0)
    doc: "系统输入电压, 原始单位 0.01V（converted 单位: V）"
  - id: file_upload_progress
    type: u1
    doc: 文件上注进度, 单位%
  - id: file_upload_check
    type: u1
    enum: file_upload_check
    doc: "文件上注校验结果, 1: 正常, 0: 异常"
  - id: normal_or_backup
    type: u1
    enum: normal_or_backup
    doc: "ECU主备系统状态, 1: 处于主flash, 2: 处于备flash"
  - id: storage_valid
    type: u2
    doc: ECU剩余储存空间, 单位MB
  - id: pl_version
    type: u1
    doc: ECU pl端固件版本号
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
    doc: "当前采数模式, 2: 事例特征量；3: 事例波形；4: 能谱特征量；5: 能谱波形；6: 事例+能谱特征量；7: 事例+能谱波形"
  - id: data_transfer_package_count
    type: u1
    doc: 数传数据包发送个数
  - id: saa_status
    type: u1
    enum: saa_status
    doc: "SAA区状态, 进入saa: 0x01; 离开saa: 0x00"
  - id: entered_saa_count
    type: u1
    doc: SAA区进入次数计数
  - id: sipm_voltage_ch0
    type: scaled(0.001, 0.0)
    doc: "SiPM 通道0电压, 原始单位 mV（converted 单位: V）"
  - id: sipm_current_ch0
    type: scaled(0.001, 0.0)
    doc: "SiPM 通道0电流, 原始单位 uA（converted 单位: mA）"
  - id: sipm_temperature_ch0
    type: scaled(0.01, -273.15)
    doc: "SiPM 通道0温度, 原始单位 10mK（converted 单位: 摄氏度）"
  - id: sipm_voltage_ch1
    type: scaled(0.001, 0.0)
    doc: "SiPM 通道1电压, 原始单位 mV（converted 单位: V）"
  - id: sipm_current_ch1
    type: scaled(0.001, 0.0)
    doc: "SiPM 通道1电流, 原始单位 uA（converted 单位: mA）"
  - id: sipm_temperature_ch1
    type: scaled(0.01, -273.15)
    doc: "SiPM 通道1温度, 原始单位 10mK（converted 单位: 摄氏度）"
  - id: sipm_voltage_ch2
    type: scaled(0.001, 0.0)
    doc: "SiPM 通道2电压, 原始单位 mV（converted 单位: V）"
  - id: sipm_current_ch2
    type: scaled(0.001, 0.0)
    doc: "SiPM 通道2电流, 原始单位 uA（converted 单位: mA）"
  - id: sipm_temperature_ch2
    type: scaled(0.01, -273.15)
    doc: "SiPM 通道2温度, 原始单位 10mK（converted 单位: 摄氏度）"
  - id: sipm_voltage_ch3
    type: scaled(0.001, 0.0)
    doc: "SiPM 通道3电压, 原始单位 mV（converted 单位: V）"
  - id: sipm_current_ch3
    type: scaled(0.001, 0.0)
    doc: "SiPM 通道3电流, 原始单位 uA（converted 单位: mA）"
  - id: sipm_temperature_ch3
    type: scaled(0.01, -273.15)
    doc: "SiPM 通道3温度, 原始单位 10mK（converted 单位: 摄氏度）"
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
  - id: sipm_hot_flag
    type: u1
    enum: sipm_hot_flag
    doc: "塑闪超温标志, 0x55=过热(卫星方断电), 0x00=正常"
  - id: heat_protect_threshold
    type: u1
    doc: "塑闪超温阈值, 默认68"
  - id: reserve
    type: u1
    repeat: expr
    repeat-expr: 20
    doc: "预留。20是为了凑总帧长度为8的倍数， 匹配长光的can帧结构，发送的时候劈开成单个的工程参数can帧"
instances:
  body_data:
    pos: 0
    type: u1
    repeat: expr
    repeat-expr: 71
enums:
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
  sipm_hot_flag:
    0x00: normal
    0x55: overheat

types:
  scaled:
    params:
      - id: scale
        type: f8
      - id: offset
        type: f8
    seq:
      - id: raw
        type: u2
        doc: "原始值（未换算）"
    instances:
      converted:
        value: raw * scale + offset
