根据《星测未来——天格地面演示系统使用说明-V1.1》，以下是关于 **HK文件** 中各个字段的描述整理：

---

# HK文件字段描述

| 序号 | 字段名 | 符号 | 起始位置 | 字节数 | 数据类型 | 参数说明 |
|------|--------|------|----------|--------|----------|----------|
| 1 | 帧头 | header | 0 | 4 | uint32 | 0x1A2B3C4D |
| 2 | UTC时间戳 | utc_time | 4 | 4 | uint32 | — |
| 3 | CPU温度检测，数字量 | cpu_temperature | 8 | 2 | uint16 | 参考温度计算方法 |
| 4 | DAQ温度检测，数字量 | daq_temperature_i2c1_0x49 | 10 | 2 | uint16 | 参考温度计算方法 |
| 5 | ecu剩余存储空间 | storage_valid | 12 | 2 | uint16 | /nvme存储空间监控，单位：1MB |
| 6 | FEE转接板，系统电源5V电路检测，ADC数字量，电压 | voltage_i2c1_0x40 | 14 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 7 | FEE转接板，系统电源5V电路检测，ADC数字量，电流 | current_i2c1_0x40 | 16 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.02Ω |
| 8 | FEE转接板，2.1V电路检测，ADC数字量，电压 | voltage_i2c1_0x41 | 18 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 9 | FEE转接板，2.1V电路检测，ADC数字量，电流 | current_i2c1_0x41 | 20 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.12Ω |
| 10 | FEE转接板，5.4V电路检测，ADC数字量，电压 | voltage_i2c1_0x42 | 22 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 11 | FEE转接板，5.4V电路检测，ADC数字量，电流 | current_i2c1_0x42 | 24 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.12Ω |
| 12 | FEE转接板，5VA电路检测，ADC数字量，电压 | voltage_i2c1_0x4D | 26 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 13 | FEE转接板，5VA电路检测，ADC数字量，电流 | current_i2c1_0x4D | 28 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.12Ω |
| 14 | FEE，5VA电路检测，ADC数字量，电压 | voltage_i2c2_0x40 | 30 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 15 | FEE，5VA电路检测，ADC数字量，电流 | current_i2c2_0x40 | 32 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.06Ω |
| 16 | FEE，1.8VA电路检测，ADC数字量，电压 | voltage_i2c2_0x41 | 34 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 17 | FEE，1.8VA电路检测，ADC数字量，电流 | current_i2c2_0x41 | 36 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.06Ω |
| 18 | FEE，3V3电路检测，ADC数字量，电压 | voltage_i2c2_0x42 | 38 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 19 | FEE，3V3电路检测，ADC数字量，电流 | current_i2c2_0x42 | 40 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.06Ω |
| 20 | FEE，1.8VD电路检测，ADC数字量，电压 | voltage_i2c2_0x43 | 42 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 21 | FEE，1.8VD电路检测，ADC数字量，电流 | current_i2c2_0x43 | 44 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.06Ω |
| 22 | FEE，P5VA_1电路检测，ADC数字量，电压 | voltage_i2c2_0x44 | 46 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 23 | FEE，P5VA_1电路检测，ADC数字量，电流 | current_i2c2_0x44 | 48 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.06Ω |
| 24 | FEE，P5VA_2电路检测，ADC数字量，电压 | voltage_i2c2_0x45 | 50 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 25 | FEE，P5VA_2电路检测，ADC数字量，电流 | current_i2c2_0x45 | 52 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.06Ω |
| 26 | FEE，P5VA_3电路检测，ADC数字量，电压 | voltage_i2c2_0x46 | 54 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 27 | FEE，P5VA_3电路检测，ADC数字量，电流 | current_i2c2_0x46 | 56 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.06Ω |
| 28 | FEE，P5VA_4电路检测，ADC数字量，电压 | voltage_i2c2_0x47 | 58 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 29 | FEE，P5VA_4电路检测，ADC数字量，电流 | current_i2c2_0x47 | 60 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.06Ω |
| 30 | DAQ，1V0电路检测，ADC数字量，电压 | voltage_i2c1_0x43 | 62 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 31 | DAQ，1V0电路检测，ADC数字量，电流 | current_i2c1_0x43 | 64 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.03Ω |
| 32 | DAQ，1V8电路检测，ADC数字量，电压 | voltage_i2c1_0x44 | 66 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 33 | DAQ，1V8电路检测，ADC数字量，电流 | current_i2c1_0x44 | 68 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.03Ω |
| 34 | DAQ，2V5电路检测（实测的是DCDC前置电压约5V），ADC数字量，电压 | voltage_i2c1_0x45 | 70 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 35 | DAQ，2V5电路检测（实测的是DCDC前置电压约5V），ADC数字量，电流 | current_i2c1_0x45 | 72 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.04Ω |
| 36 | DAQ，3V3电路检测，ADC数字量，电压 | voltage_i2c1_0x47 | 74 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 37 | DAQ，3V3电路检测，ADC数字量，电流 | current_i2c1_0x47 | 76 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.03Ω |
| 38 | DAQ，1V5电路检测，ADC数字量，电压 | voltage_i2c1_0x48 | 78 | 2 | int16 | 模拟量 = 数字量 * 1.25mV |
| 39 | DAQ，1V5电路检测，ADC数字量，电流 | current_i2c1_0x48 | 80 | 2 | int16 | 模拟量 = 数字量 * 2.5μV / 0.075Ω |
| 40 | SIPM通道0电压 | voltage_sipm_ch0 | 82 | 2 | uint16 | 单位：mV |
| 41 | SIPM通道0电流 | current_sipm_ch0 | 84 | 2 | uint16 | 单位：μA |
| 42 | SIPM通道0温度 | temperature_sipm_ch0 | 86 | 2 | uint16 | Tc = 数字量/100 - 273.15，Tc为摄氏度 |
| 43 | SIPM通道1电压 | voltage_sipm_ch1 | 88 | 2 | uint16 | 单位：mV |
| 44 | SIPM通道1电流 | current_sipm_ch1 | 90 | 2 | uint16 | 单位：μA |
| 45 | SIPM通道1温度 | temperature_sipm_ch1 | 92 | 2 | uint16 | Tc = 数字量/100 - 273.15，Tc为摄氏度 |
| 46 | SIPM通道2电压 | voltage_sipm_ch2 | 94 | 2 | uint16 | 单位：mV |
| 47 | SIPM通道2电流 | current_sipm_ch2 | 96 | 2 | uint16 | 单位：μA |
| 48 | SIPM通道2温度 | temperature_sipm_ch2 | 98 | 2 | uint16 | Tc = 数字量/100 - 273.15，Tc为摄氏度 |
| 49 | SIPM通道3电压 | voltage_sipm_ch3 | 100 | 2 | uint16 | 单位：mV |
| 50 | SIPM通道3电流 | current_sipm_ch3 | 102 | 2 | uint16 | 单位：μA |
| 51 | SIPM通道3温度 | temperature_sipm_ch3 | 104 | 2 | uint16 | Tc = 数字量/100 - 273.15，Tc为摄氏度 |
| 52 | saa区判定方式 | saa_judge_method | 106 | 1 | uint8 | 低4位表示SAA区判定方式；bit4表示进出SAA区是否切换观测模式，1:不切换；0:切换；0x00:依据SAA区状态指令判定SAA区状态，并使能模式切换；0x01:依据广播的星下经纬度进行重计算得到的SAA区状态，并使能模式切换；0x02:依据计数率阈值判断SAA区状态，并使能模式切换；0x10:依据SAA区状态指令判定SAA区状态，并失能模式切换；0x11:依据广播的星下经纬度进行重计算得到的SAA区状态，并失能模式切换；0x12:依据计数率阈值判断SAA区状态，并失能模式切换 |
| 53 | GPS广播-UTC累计秒 | gps_seconds | 107 | 4 | uint32 | 基准时间2000年1月1日12时0秒 |
| 54 | GPS广播-WGS-84坐标系位置-X | wgs_84_pos_x | 111 | 4 | int32 | 单位：米，权重：0.01/bit |
| 55 | GPS广播-WGS-84坐标系位置-Y | wgs_84_pos_y | 115 | 4 | int32 | 单位：米，权重：0.01/bit |
| 56 | GPS广播-WGS-84坐标系位置-Z | wgs_84_pos_z | 119 | 4 | int32 | 单位：米，权重：0.01/bit |
| 57 | GPS广播-WGS-84坐标系速度-X | wgs_84_speed_x | 123 | 4 | int32 | 单位：米/秒，权重：0.01/bit |
| 58 | GPS广播-WGS-84坐标系速度-Y | wgs_84_speed_y | 127 | 4 | int32 | 单位：米/秒，权重：0.01/bit |
| 59 | GPS广播-WGS-84坐标系速度-Z | wgs_84_speed_z | 131 | 4 | int32 | 单位：米/秒，权重：0.01/bit |
| 60 | 星敏1-数据有效性标识 | xingmin1_valid | 135 | 1 | uint8 | 1=有效；0=无效 |
| 61 | 星敏1-UTC累计秒 | xingmin1_seconds | 136 | 4 | uint32 | 基准时间2000年1月1日12时0秒 |
| 62 | 星敏1-毫秒 | xingmin1_microseconds | 140 | 2 | int16 | 曝光时差 |
| 63 | 星敏1-q1 | xingmin1_q0 | 142 | 4 | int32 | 矢量；当量：1/2147483647，（星敏坐标系相对于J2000惯性坐标系）负数用补码形式表示 |
| 64 | 星敏1-q2 | xingmin1_q1 | 146 | 4 | int32 | 同上 |
| 65 | 星敏1-q3 | xingmin1_q2 | 150 | 4 | int32 | 同上 |
| 66 | 星敏1-q4 | xingmin1_q3 | 154 | 4 | int32 | 标量；当量：1/2147483647，（星敏坐标系相对于J2000惯性坐标系）为正数 |
| 67 | 星敏2-数据有效性标识 | xingmin2_valid | 158 | 1 | uint8 | 1=有效；0=无效 |
| 68 | 星敏2-UTC累计秒 | xingmin2_seconds | 159 | 4 | uint32 | 基准时间2000年1月1日12时0秒 |
| 69 | 星敏2-毫秒 | xingmin2_microseconds | 163 | 2 | int16 | 曝光时差 |
| 70 | 星敏2-q0 | xingmin2_q0 | 165 | 4 | int32 | 矢量；当量：1/2147483647，（星敏坐标系相对于J2000惯性坐标系）负数用补码形式表示 |
| 71 | 星敏2-q1 | xingmin2_q1 | 169 | 4 | int32 | 同上 |
| 72 | 星敏2-q2 | xingmin2_q2 | 173 | 4 | int32 | 同上 |
| 73 | 星敏2-q3 | xingmin2_q3 | 177 | 4 | int32 | 标量；当量：1/2147483647，（星敏坐标系相对于J2000惯性坐标系）为正数 |
| 74 | 星下点经度 | longitude | 181 | 2 | int16 | 单位：度，权重：0.01/bit |
| 75 | 星下点纬度 | latitude | 183 | 2 | int16 | 单位：度，权重：0.01/bit |
| 76 | CRC16 | crc16 | 185 | 2 | uint16 | 从header开始到crc16前一个字节计算得到的crc16值 |

> 注：
> - 所有数据均采用大端序。
> - 文件以二进制流形式存储。
> - HK文件编号与log日志文件编号一一对应。
> - 温度转换公式详见文档附录。