# -*- mode: yaml -*-
meta:
  id: grid11b_telemetry_packet
  title: GRID-11B 遥测数据包
  application: GRID Payload Monitor
  endian: be
  ks-version: "0.9"
doc: |
  GRID-11B 遥测数据包（源: xml/grid_packet.xml 的 <grid11b_telemetry_packet>）。
  - packet_len=96, 帧头 0x48 0x45 0x41 0x44 ("HEAD"), 帧尾 0x54 0x41 0x49 0x4C ("TAIL")
  - 布局核对: 固定字段 + reserve(22) + tail(4) = 96 ✓
seq:
  - id: header
    type: u4
    doc: 帧头 0x48454144 ("HEAD")
  - id: current_can_bus
    type: u1
    doc: 当前 CAN 总线
  - id: telemetry_count
    type: u1
    doc: 遥测计数
  - id: cmd_count
    type: u1
    doc: 指令计数
  - id: latest_received_cmd
    type: u1
    doc: 最近收到的指令
  - id: latest_received_cmd_progress
    type: u1
    doc: 最近收到指令的进度
  - id: latest_complete_cmd
    type: u1
    doc: 最近完成的指令
  - id: latest_complete_cmd_arg
    type: u1
    repeat: expr
    repeat-expr: 4
    doc: 最近完成指令的参数（4 字节）
  - id: latest_complete_cmd_exit
    type: u1
    doc: 最近完成指令的退出码
  - id: utc_time
    type: u4
    doc: UTC 时间戳
  - id: cpu_temperature
    type: u1
    doc: CPU 温度
  - id: daq_temperature_i2c1_0x49
    type: u1
    doc: DAQ 温度（I2C1 0x49）
  - id: system_power
    type: u2
    doc: 系统功率
  - id: system_input_voltage
    type: u2
    doc: 系统输入电压
  - id: file_upload_progress
    type: u1
    doc: 文件上传进度
  - id: file_upload_check
    type: u1
    doc: 文件上传校验
  - id: normal_or_backup
    type: u1
    doc: 正常/备份标志
  - id: storage_avaliable
    type: u2
    doc: 可用存储（原 XML 拼写 storage_avaliable）
  - id: pl_version
    type: u1
    doc: PL 版本
  - id: app_version
    type: u1
    doc: APP 版本
  - id: log_index
    type: u1
    doc: 日志索引
  - id: sci_data_index
    type: u1
    doc: 科学数据索引
  - id: sample_mode
    type: u1
    doc: 采样模式
  - id: data_transfer_package_count
    type: u1
    doc: 数据传输包计数
  - id: saa_status
    type: u1
    doc: SAA 状态
  - id: entered_saa_count
    type: u1
    doc: 进入 SAA 计数
  - id: sipm_voltage_ch0
    type: u2
    doc: SiPM 通道 0 偏压
  - id: sipm_current_ch0
    type: u2
    doc: SiPM 通道 0 电流
  - id: sipm_temprature_ch0
    type: u2
    doc: SiPM 通道 0 温度（原 XML 拼写 sipm_temprature_ch0）
  - id: sipm_voltage_ch1
    type: u2
    doc: SiPM 通道 1 偏压
  - id: sipm_current_ch1
    type: u2
    doc: SiPM 通道 1 电流
  - id: sipm_temprature_ch1
    type: u2
    doc: SiPM 通道 1 温度
  - id: sipm_voltage_ch2
    type: u2
    doc: SiPM 通道 2 偏压
  - id: sipm_current_ch2
    type: u2
    doc: SiPM 通道 2 电流
  - id: sipm_temprature_ch2
    type: u2
    doc: SiPM 通道 2 温度
  - id: sipm_voltage_ch3
    type: u2
    doc: SiPM 通道 3 偏压
  - id: sipm_current_ch3
    type: u2
    doc: SiPM 通道 3 电流
  - id: sipm_temprature_ch3
    type: u2
    doc: SiPM 通道 3 温度
  - id: count_rate0
    type: u2
    doc: 计数率 0
  - id: count_rate1
    type: u2
    doc: 计数率 1
  - id: count_rate2
    type: u2
    doc: 计数率 2
  - id: count_rate3
    type: u2
    doc: 计数率 3
  - id: reserve
    type: u1
    repeat: expr
    repeat-expr: 22
    doc: 保留字段（22 字节）
  - id: tail
    type: u4
    doc: 帧尾 0x5441494C ("TAIL")
