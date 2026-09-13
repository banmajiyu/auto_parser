# Kaitai Struct

> Kaitai Struct（KSY）：一种用 YAML 声明二进制格式、自动生成多语言解析器的**声明式二进制解析工具**（declarative binary parsing）。核心价值是"写一次 `.ksy` 描述，生成 C++/C#/Go/Java/JavaScript/Python 等各语言解析器"，把**格式描述**与**解析实现**分离。官方文档见 [doc.kaitai.io/user_guide.html](https://doc.kaitai.io/user_guide.html)。

## 核心结论

1. `.ksy` 由四段构成：`meta`（元信息）→ `seq`（顶层顺序解析）→ `types`（自定义类型）→ `instances`（惰性附加字段）。
2. 字段校验有**两种截然不同的机制**：`valid`（运行时断言，失败抛错）与 `contents`（固定字节序列匹配，常用于帧头/帧尾 magic）。
3. 读取字段默认走 `seq` 顺序解析；用 `instances` + `pos` 可从任意偏移重新切入、惰性取原始字节。
4. Kaitai Struct 是**纯解析器**：CRC 校验、奇偶/异或校验等**不属于**其能力范围，需拆分到外部校验逻辑（见 §8）。
5. 类型系统由标量类型（整型/浮点/字符串/字节）+ `enums`（整数→具名常量）+ 用户自定义类型 + `switch-on`（条件类型）构成。
6. `ksc` 编译器把 `.ksy` 生成目标语言解析器；`process` 提供 `xor`/`zlib` 等字节变换，用于解析侧的解码/还原。

---

## 1. 四段式骨架

```yaml
meta:        # 元信息
  id: frameseq
  endian: be
seq:         # 顶层顺序解析
  - id: frames
    type: frame
    repeat: eos
types:       # 自定义类型
  frame:
    seq:
      - id: header
        type: u4
instances:   # 惰性附加字段（可选）
  body_data:
    pos: 0
    type: u1
```

- **`meta`**：描述整个文件，最常用的键是 `id`（生成的类型名）、`endian`（字节序）、`file-extension`（目标扩展名，如 `.hk`）。
- **`seq`**：顶层要**顺序读取**的字段列表，每个字段至少要有 `id` 与 `type`。
- **`types`**：自定义类型的字典，供 `seq` 里以 `type: xxx` 引用；类型内部也有自己的 `seq`/`instances`。
- **`instances`**：**惰性**字段——不在顺序流里按位置读取，而是在被访问时才计算/读取，常用于"另起一个视角看同一份数据"（详见 §9）。

## 2. 整数类型与字节序

| 关键字 | 含义 | 字节数 | 取值范围（有符号） |
|---|---|---|---|
| `u1` / `u2` / `u4` / `u8` | 无符号整数 | 1 / 2 / 4 / 8 | — |
| `s1` / `s2` / `s4` / `s8` | 有符号整数 | 1 / 2 / 4 / 8 | 见注释 |

- 数字后缀即**字节数**：`u2` 是 2 字节无符号，`s2` 是 2 字节有符号。
- 示例 2 中电流字段用 `s2`（`current_i2c1_0x40` 等），因为电流有正负方向；电压同类字段也统一用 `s2`，无符号量（`u2`）则用于纯正值（如 SiPM 通道电压/电流/温度）。
- **`endian: be`**：大端（big-endian）——高位字节在前。写 `.ksy` 时若实际文件是大端，务必声明 `be`，否则所有多字节整数解析都会错位；小端用 `endian: le`。

## 3. 枚举 `enums`

`enums:` 是顶层段（与 `meta`/`seq`/`types` 平级），把**整数值映射为具名常量**，让解析输出从"裸数字"变成可读的名字（见 [用户指南 Enums](https://doc.kaitai.io/user_guide.html#_enums)）。

```yaml
enums:
  opcode:
    0: add
    1: sub
    2: mul
```

字段通过 `enum: <枚举名>` 关联：

```yaml
- id: op
  type: u1
  enum: opcode
```

- 解析时字段按 `type`（这里是 `u1`）读出整数，再用枚举表匹配成名字。
- **未列出的值**保留为原始整数（各语言行为略有差异，见 [issue #778](https://github.com/kaitai-io/kaitai_struct/issues/778)）。
- 枚举的底层整数类型由**引用它的字段的 `type`** 决定（读成 `u1` 就以 `u1` 匹配）。
- 典型用途：状态码 / 类型码 / 命令字。示例 2 里的 `saa_judge_method`、`storage_valid` 这类字段若有码表，就该定义枚举让输出可读。

## 4. 类型系统 `type`

`type:` 是每个字段（`seq` 或 `instances` 里的条目）必须有的属性，取值分三类：

### 4.1 标量类型

| 类别  | 关键字                   | 说明                                   |
| --- | --------------------- | ------------------------------------ |
| 整数  | `u1`~`u8` / `s1`~`s8` | 见 §2                                 |
| 浮点  | `f4` / `f8`           | 4 / 8 字节 IEEE 754 浮点                 |
| 字节串 | `bytes`               | 定长原始字节，需配 `size:`                    |
| 字符串 | `str` / `strz`        | 定长字符串 / 以 `\0` 结尾的字符串，需配 `encoding:` |

- 示例里的 `body_data` 用 `type: u1` + `repeat: expr` 拼出一个字节数组——等价于取定长 `bytes`，但用 `repeat` 写法更直观。

### 4.2 用户自定义类型

- 在 `types:` 里定义，字段用 `type: <类型名>` 引用。
- 类型可**递归组合**：示例 1 的 `frame.seq` 里 `events` 引用了 `event`；示例 2 里 `frame_and_unknown` 组合了 `frame` 与 `unknown`。
- 引用即"嵌套解析"：该字段会按目标类型的 `seq` 顺序解析成一个子对象。

### 4.3 条件类型 `switch-on`

当"字段该读成什么类型"取决于前面某个字段的值时，用 `switch-on`（见 [Repeats, Switches, and Process Transforms](https://deepwiki.com/kaitai-io/kaitai_struct_tests/7.3-repeats-switches-and-process-transforms)）：

```yaml
- id: body
  type:
    switch-on: kind
    cases:
      1: type_a
      2: type_b
      _: type_default
```

- `switch-on` 后接一个**字段 id**，`cases` 映射"值 → 类型名"；`_` 分支作默认。
- 把"按类型码分派结构"的 switch 逻辑从手写解析代码搬进声明式描述，适合"帧头里有个类型码，决定帧体结构"的协议。

## 5. 重复字段 `repeat`

`repeat` 控制"这个字段连续出现几次"，常见三种写法：

1. **`repeat: eos`**：一直读到流末尾（end of stream），用于"文件里剩下的都是这种结构"。两个示例顶层的 `frames` 都是 `repeat: eos`——文件主体就是不定长的帧序列。
2. **`repeat: expr` + `repeat-expr: N`**：固定重复 N 次（表达式求值为 N）。两个示例里的 `41`、`78`、`522`、`107` 都是这种：`events` 每帧 41 个事件、`unknown` 每帧 78 字节未知块、`body_data` 固定 522 或 107 字节。
3. **`repeat: until` + `repeat-until: 条件`**：重复直到某条件成立（本例未出现，属常见补充）。

> 关键区别：`repeat: eos` 是**吃到边界**，`repeat: expr` 是**吃到计数**。前者适合"流里剩下多少读多少"，后者适合"协议写死了定长块"。

## 6. 字段校验：`valid` vs `contents`

### 6.1 `valid`：运行时断言

```yaml
- id: header
  type: u4
  valid:
    eq: 0x1c1c2288
```

- 语义：解析完成后**校验该字段的值**满足条件，不满足则**抛异常**（解析失败）。
- `valid` 支持 `eq`（等于）、`not_eq`、`min`、`max`、`any_of`、`expr`（任意表达式）等操作符；也可直接写成一个布尔表达式（见 §6.3）。
- 用途：**格式自校验**——示例 1 用它保证帧头 `0x1c1c2288`，一旦不匹配立即报错，而不是悄悄解析出垃圾数据。

### 6.2 `contents`：固定字节序列匹配

```yaml
- id: tail
  type: u4
  contents: [0xcc, 0x11, 0x88, 0x22]
```

- 语义：**预先声明**该字段在文件里**固定为**这串字节（magic bytes），解析器据此校验并可直接断言。
- 官方关键字是 **`contents`（复数）**——例如 [gzip 格式规范](https://formats.kaitai.io/gzip/) 里写 `contents: [0x1f, 0x8b]` 匹配 gzip 魔数。
- 用途：帧头/帧尾等**固定魔数**；示例 2 帧头 `[0x1a, 0x2b, 0x3c, 0x4d]` 与示例 1 帧尾 `[0xcc, 0x11, 0x88, 0x22]` 都属此类。

> ⚠️ **笔误提醒**：用户提供的示例写的是 `content:`（单数）。Kaitai Struct 官方关键字是 `contents:`（复数）。单数 `content:` 会被编译器视为未知键（见 [issue #501](https://github.com/kaitai-io/kaitai_struct/issues/501)），**落地前务必改成 `contents:`**。

### 6.3 帧头/帧尾校验：何时用哪个

检验帧头（Header）和帧尾（Trailer）时，`contents` 和 `valid` 的差异主要体现在**匹配时机、字节消耗方式以及灵活性**上。

**① 用 `contents` —— 固定字节序列的直接匹配**

- **适用场景**：帧头/帧尾是**完全固定的字节序列**（如 `0xAA 0xBB` 起始标记、`0xCC 0xDD` 结束标记）。
- **行为**：解析器**自动读取**与给定序列等长的字节并逐字节比较；匹配则消耗掉这些字节，后续字段从下一字节开始；不匹配立即抛异常。
- **优点**：简洁、零开销，无需额外表达式，天然保证帧结构完整。
- **示例**（帧头 `0xFE 0xED`，帧尾 `0xBE 0xEF`）：

```yaml
seq:
  - id: header_magic
    contents: [0xFE, 0xED]
  - id: payload
    size: 10
  - id: trailer_magic
    contents: [0xBE, 0xEF]
```

**② 用 `valid` —— 对已解析值的条件验证**

- **适用场景**：帧头/帧尾不是固定字节序列，而是**由其他字段解析出的值**（如 `u2` 类型帧头 ID 取值 100~200）；帧尾是校验和/CRC 等需**动态计算验证**的值；长度不固定但可由长度字段确定。
- **行为**：字段先按 `type` 正常解析（消耗相应字节），解析完成后检查 `valid` 布尔表达式，为 `false` 则抛验证异常；**不改变字节读取方式**，只是事后检查。
- **优点**：灵活，可表达复杂约束（范围、枚举、跨字段关系）。
- **示例**（帧头是 `u2`，必须等于 `0x1234` 或 `0x5678`）：

```yaml
seq:
  - id: frame_header
    type: u2
    valid: frame_header == 0x1234 or frame_header == 0x5678
```

帧尾是 CRC16 校验值，需与计算值相等（`calc_crc` 为**伪代码**，CRC 计算非 KSY 内置能力，见 §8）：

```yaml
seq:
  - id: stored_crc
    type: u2
    valid: stored_crc == computed_crc
instances:
  computed_crc:
    value: calc_crc(payload)
```

**③ 核心对比表**

| 特性 | `contents` | `valid` |
|---|---|---|
| 匹配目标 | 原始字节流（固定序列） | 已解析的值（整数、枚举、字符串等） |
| 字节消耗 | 自动消耗与序列等长的字节 | 由字段的 `type`/`size` 决定 |
| 匹配时机 | 解析该字段时即时匹配 | 字段解析完成后条件检查 |
| 能否表达动态约束 | 不能（必须硬编码字节值） | 能（算术、逻辑、跨字段引用） |
| 典型帧头帧尾用途 | 固定魔数、同步头 | 版本号范围、协议标识符枚举、校验和验证 |

**④ 实际选择建议**

- **固定不变的帧头/帧尾** → 优先 `contents`：更直观、性能更好，无需额外解析步骤。
- **需按上下文动态判定**（不同版本不同帧头，或帧尾是计算出的校验码）→ 用 `valid` 配合表达式。
- **定长但值不固定的帧头/帧尾**（如 `u2` 类型、取值只能是少数几个枚举值）→ 用 `valid`，因 `contents` 无法表达"等于多个值之一"。

> 结论：**`contents` 适合"硬匹配"，`valid` 适合"软约束"**。

## 7. 过程变换与校验 `process`

`process` 是字段级属性，在**读取时对原始字节流做变换**再得到字段值，常用于解析侧的解码/还原（见 [用户指南 Process](https://doc.kaitai.io/user_guide.html#_processing_byte_arrays)）。它操作的是**字节**，不是**数值**。

### 7.1 支持的变换

| process | 作用 | 示例 |
|---|---|---|
| `xor(key)` | 逐字节与 key 异或 | `process: xor(0xff)` |
| `rol(n)` / `ror(n)` | 循环左移 / 右移 n 位（按字节） | `process: ror(3)` |
| `invert` | 逐字节按位取反（`~b`） | `process: invert` |
| `zlib` | zlib 解压 | `process: zlib` |

```yaml
- id: payload
  size: 8
  process: xor(0xff)
```

- `process` 作用于**原始字节**：如 `xor(0xff)` 是把读到的 8 个字节逐个与 `0xff` 异或后再解释为字段值。
- `process` 可以按 `xor(0xaa) -> ror(3)` 的写法**串接多步**变换（从左到右依次应用）。
- 适用场景：数据在传输/存储时被"搅乱"（XOR 混淆、位旋转、取反）或压缩（zlib），需要在解析时还原。
- **自定义例程**：v0.8+ 支持 `process: my_routine(...)` 调用自定义处理例程，但该例程的实现需为目标语言单独编写（见 §8.1）。

### 7.2 `process` 与「奇偶异或校验」不是一回事

- `process: xor` 是**逐字节 XOR 一个固定 key 的解码变换**，还原后字段值可读。
- 日记里提到的"奇偶异或校验"是**把所有字节异或累加出一个校验和的校验算法**——属于语义校验，KSY 本身不做（见 §8）。

### 7.3 数值换算 ≠ `process`（关键区分）

> **重要**：`process` 只能做**字节级**变换，**不能做数值的算术换算**。开氏度转摄氏度（`℃ = K − 273.15`）、原始 ADC 值乘以比例系数这类"字面量转换"是**对已解析数值的计算**，属于 `instances` 的 `value:` 表达式（见 §7.4），不属于 `process`。

这是两者最容易混淆的地方：

|         | `process`           | `instances` + `value:`   |
| ------- | ------------------- | ------------------------ |
| 操作对象    | **原始字节流**           | **已解析的字段值**              |
| 能做      | XOR / 位旋转 / 取反 / 解压 | 算术（`+ − * /`）、类型转换、跨字段运算 |
| 典型用例    | 解码混淆的字节             | 单位换算、比例换算、派生字段           |
| 开氏度转摄氏度 | ❌ 做不到               | ✅ 用表达式                   |

### 7.4 字面量/单位换算：`instances` 的 `value:` 表达式

`value:` 是 `instances` 的一种写法——**不从流读取，而是用表达式计算一个派生字段**（见 [Expressions, Navigation, and Instances](https://deepwiki.com/kaitai-io/kaitai_struct_tests/7.2-expressions-navigation-and-instances)）。

**开氏度转摄氏度**（原始字段 `temp_raw` 存开氏度，派生字段 `temp_c` 存摄氏度）：

```yaml
seq:
  - id: temp_raw
    type: u2          # 原始开氏度，如 29315（×100 定点）
instances:
  temp_c:
    value: (temp_raw - 27315) / 100.0   # 转摄氏度
```

- `value:` 里的表达式引用**已解析字段的 id**（如上例的 `temp_raw`），支持 `+ − * / %`、比较、逻辑、三元 `? :` 等运算符。
- 惰性：只有访问 `temp_c` 时才计算，不访问不花代价。
- 常见换算都能这样写：
  - 单位换算：`value: voltage_raw * 0.001`（毫伏 → 伏）
  - 比例换算：`value: adc * 3.3 / 4095`（ADC 码值 → 电压）
  - 定点数还原：`value: fixed_q * 0.01`（定点小数 → 浮点）
  - 派生字段：`value: end_pos - start_pos`（跨字段算长度）

### 7.5 两种"转换"如何搭配（贴合卫星数据）

对温度这类量，常见做法是**原始字段 + 派生字段并存**：

```yaml
seq:
  - id: cpu_temperature_raw
    type: u2                    # 板上原始值（开氏度 ×100 定点）
  - id: voltage_sipm_ch0
    type: u2                    # 原始 ADC 码值
instances:
  cpu_temperature_c:
    value: (cpu_temperature_raw - 27315) / 100.0   # 开氏度 → 摄氏度
  voltage_sipm_ch0_v:
    value: voltage_sipm_ch0 * 3.3 / 4095          # ADC → 电压
```

- `seq` 保留**原始字段**（`_raw` 后缀），保证二进制结构完整可回放；
- `instances` 加**派生字段**（`_c`、`_v` 后缀），给下游消费方直接可读的物理量。
- 这正是日记里"把字面量转换写入 ksy 语义验证"的落点——转换放在 `.ksy` 里做，而不是丢给下游代码。

### 7.6 对大量字段做同一转换：用 `type` 复用

当几十个字段都要做同一种换算时，逐个写 `instances.value` 会重复。标量类型（`u2`）本身**不能挂算术换算**，但可以用**自定义 `type`** 把"读原始值 + 换算"封装成一个可复用的单位。

**① 完全相同换算 → 无参自定义类型**

```yaml
types:
  celsius:                  # 定义"读开氏度×100 → 换算成摄氏"的类型
    seq:
      - id: raw
        type: u2            # 原始值：开氏度 ×100 定点
    instances:
      c:
        value: (raw - 27315) / 100.0

seq:
  - id: cpu_temperature
    type: celsius           # 所有温度字段都引用同一类型
  - id: daq_temperature_i2c1_0x49
    type: celsius
```

- 引用后每个字段都是 `celsius` 对象，访问原始值 `cpu_temperature.raw`、换算值 `cpu_temperature.c`。
- **代价**：字段从标量 `int` 变成了对象，下游访问路径多一层（`.raw` / `.c`）。

**② 换算参数不同 → 参数化类型 `params`**

同一换算公式、但比例/偏移各字段不同时，用 `params` 把参数传进去（见 [Parametric types issue #192](https://github.com/kaitai-io/kaitai_struct/issues/192)）：

```yaml
types:
  scaled:
    params:
      - id: scale
        type: f8          # 比例系数
      - id: offset
        type: f8          # 偏移
    seq:
      - id: raw
        type: u2
    instances:
      v:
        value: raw * scale + offset

seq:
  - id: temp_k
    type: scaled(0.01, -273.15)      # ×100 定点：开氏→摄氏
  - id: volt_mv
    type: scaled(0.001, 0.0)         # 毫伏→伏
```

- 引用写法：`type: scaled(0.01, -273.15)` 为**位置参数**，按 `params` 声明顺序对应；也可 `type: scaled(scale: 0.01, offset: -273.15)` 用**命名参数**。
- 同一 `scaled` 类型被所有"线性换算"字段复用，公式只写一次。

> **精度提醒**：`value` 里的 `/` 与 `*` 在 Python 目标下是浮点运算；但 C++/Java 等目标里 `int / int` 会**截断为整数**。若要多语言一致，用浮点字面量（`100.0`、`0.01`）或把参数声明为 `f8` 规避整数除法。

## 8. 校验边界：CRC 与奇偶/异或

> 以下结论来自项目实战记录（见「相关」），是踩坑后的定位。

1. **Kaitai Struct 是纯解析器**：它负责"从字节流按格式描述提取字段"，**不做** CRC 校验、奇偶/异或校验这类**语义校验**——`calc_crc` 之类函数**不是** KSY 内置能力。
2. **正确的流水线是 `parse → validate → write`**：KSY 只承担 `parse`；`validate` 阶段（CRC、奇偶异或）由额外的校验类完成。
3. **KSY 语义验证内可承担的**：校验开关（`valid` 表达式）、字面量转换、可变包长度——这些属于"格式层"的可变控制；剩余的校验工作剥离到外部类。
4. **不要"侵入式改 KSY 语法"**：早期曾修改 KSY 语法硬塞校验逻辑，后来确认是错误方案；标准 `.ksy` 才是可维护的选择。
5. **落地建议**：用 `instances` 整块取出帧体（`body_data`），把原始字节喂给外部 CRC/奇偶异或校验函数比对 `stored_crc`，而不是试图在 `.ksy` 内实现校验算法。

### 8.1 KSY 表达式里"调用函数"的边界

> 这是"校验逻辑放哪"的延伸：`.ksy` 是声明式的、**语言中立**的，它不认识你的 Python 函数。

- **能在 `.ksy` 里调用**：
  - Kaitai 表达式语言的内置方法（如 `size`、`length`、`to_s` 等）；
  - 通过 `process` 注册的**自定义处理例程**（v0.8+，语法 `process: my_routine(...)`，但例程实现必须为目标语言单独编写，见 §7.1）。
- **不能直接调用**：任意目标语言函数/库——如 `zlib.crc32`、你写的 `calc_crc`。Kaitai 不知道 Python 的 `zlib` 是什么，写 `value: calc_crc(payload)` 是**不合法**的（编译器不认识 `calc_crc`）。
- **实用建议（方式 C，最常用）**：复杂校验（CRC32/MD5/奇偶异或）**别硬塞进 `.ksy`**。让 `instances` 把原始字节"透传"出来（见 §9.6），在 Python 侧写校验函数比对。

> 💡 判定标准：如果"外部函数"能用 Kaitai 表达式（算术、比较、位运算、内置方法）表达，就写进 `.ksy`；涉及复杂算法或调用第三方库，就由 `instances` 暴露数据、在目标语言侧计算。

## 9. `instances`：惰性字段与 `pos` 重定位

### 9.1 什么是惰性字段

`instances` 里的字段是**惰性（lazy）字段**：与 `seq` 顺序字段最大的区别是——**不会在解析主序列时自动求值，而是在首次被显式访问时才计算/解析**（按需加载），之后缓存结果。

| | `seq` 顺序字段 | `instances` 惰性字段 |
|---|---|---|
| 求值时机 | `_read()` 中立即解析 | 首次访问时解析并缓存 |
| 对象上的表现 | 普通属性 | 也是属性（`@property`），外部用法无差别 |
| 是否消耗 IO | 是（按定义顺序） | 按需，可能 `seek` 到指定位置 |
| 能否引用"后面的字段" | 不能（尚未解析） | 能（访问时 seq 已全部就绪） |

> 你之前"误以为惰性字段和普通字段混在一起"的感觉是对的——**从使用者的角度看它们都是同一对象的属性**（`obj.field`），区别只在内部机制：一个是 eager、一个是 lazy。

好处：避免一次性解析所有可能用不到的字段，适合可选数据块、大型数组、条件跳转场景。

### 9.2 两种惰性字段

| 类型 | 关键字 | 描述 |
|---|---|---|
| 值实例（Value Instance） | `value:` | 直接给表达式，返回计算结果，**不消耗输入流字节** |
| IO 实例（IO Instance） | `pos:`/`size:`/`io:` + `type:` | 基于输入流的某个子区域解析，可嵌套复杂类型 |

- 示例里的 `body_data`（`pos: 0` + `repeat: expr`）就是 IO 实例；§7.4 的 `temp_c`（`value:`）就是值实例。

### 9.3 `instances` 的属性清单

**通用属性**：

- `doc` / `doc-ref` — 文档注释 / 外部文档引用。

**值实例专用**：

- `value` — 必填，一个表达式（常量、算术、对其他字段的引用）。例：

```yaml
instances:
  my_sum:
    value: field_a + field_b
  is_valid:
    value: header.magic == 0xabcd
```

**IO 实例专用**：

- `pos` — 在该流中的起始偏移（字节）。
- `size` — 读取的字节数（省略则读到流末尾）。
- `io` — 自定义输入流来源（表达式），默认当前对象的根流（`_root._io`）。
- `type` — 必填，指定如何解析这段字节。
- `enum` — 若 `type` 是整数，可映射为枚举。
- `if` — 条件表达式，为真才创建该实例，否则返回 `None`。

**IO 实例进阶（可选）**：

- `process` — 后处理变换（XOR/zlib 等，见 §7）。
- `terminator` / `include` / `pad-right` / `encoding` — 字符串相关（可变长字符串）。

### 9.4 生成代码里长什么样（Python）

每个惰性字段生成一个 `@property`，首次访问时执行逻辑并缓存到 `_m_xxx`：

```python
@property
def optional_ext(self):
    if not hasattr(self, '_m_optional_ext'):   # 未加载才解析
        if (self.flags & 1) != 0:
            self._io.seek(5 + self.length)
            self._m_optional_ext = self._io.read_u4le()
        else:
            self._m_optional_ext = None
    return self._m_optional_ext               # 之后直接返回缓存
```

- Python 用 `@property`，Java 用 `public Type fieldName()`，命名因语言而异。
- **没有公开的 `_is_loaded()` 方法**；Python 侧可用 `hasattr(obj, '_m_xxx')` 判断是否已加载。
- `seq` 字段在 `_read()` 中直接 `self.field = ...` 赋值；二者在对象上**无法从外部区分**（见 §9.1 对照表）。

### 9.5 典型应用场景

1. **按需解析的可选块**：标志位指示扩展头是否存在，只在为真时解析（`if:`）。
2. **缓存计算结果**：校验和/哈希只在首次访问时计算，之后返回缓存（值实例）。
3. **安全引用后续字段**：惰性字段在 seq 解析完成后才求值，可引用 seq 中靠后的字段（seq 顺序字段不允许前向引用）。

### 9.6 完整示例：带校验的数据包 `packet.ksy`

格式：`magic(2) + length(2) + flags(1) + payload(length) + [optional_ext(4)] + stored_checksum(2)`，其中 `optional_ext` 仅当 `flags` 最低位为 1 时存在。

```yaml
meta:
  id: packet
  endian: le
seq:
  - id: magic
    contents: [0xAA, 0xBB]
  - id: length
    type: u2
  - id: flags
    type: u1
  - id: payload
    size: length            # 原始字节，length 字节
instances:
  optional_ext:             # 惰性 IO 实例：仅当 flags 最低位为 1 时存在
    pos: 5 + length         # magic(2)+length(2)+flags(1)+payload(length)
    size: 4
    type: u4
    if: (flags & 1) != 0
  stored_checksum:          # 惰性 IO 实例：存储在包尾的 CRC-16
    pos: 5 + length + ((flags & 1) != 0 ? 4 : 0)
    size: 2
    type: u2
```

> 偏移注意：magic 2 + length 2 + flags 1 = **5**（不是 6）。Kaitai 的三元运算是 `条件 ? 真值 : 假值`（不是 Python 的 `a if c else b`）。

Python 使用（CRC 在 Python 侧计算）：

```python
from packet import Packet
from kaitaistruct import KaitaiStream, BytesIO

def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc

pkt = Packet(KaitaiStream(BytesIO(raw)))

print(pkt.magic.hex(), pkt.length, pkt.flags, pkt.payload)  # seq：立即可用
print(pkt.optional_ext)      # instances：首次访问才解析；flags 为 0 时为 None
print(pkt.stored_checksum)

# 校验：CRC 在 Python 侧算，与 stored_checksum 比对
if crc16(pkt.payload) != pkt.stored_checksum:
    raise ValueError("CRC mismatch")
```

> 关键：`.ksy` 只负责"把 payload 原始字节 + stored_checksum 暴露出来"（惰性字段），**CRC 计算在 Python 侧完成**（见 §8.1）。不要在 `.ksy` 里写 `value: calc_crc(payload)`——那是不合法的。

### 9.7 惰性字段用于校验的落地要点

- 用 IO 实例（`pos` + `size`）把**待校验的原始字节**整块取出（如 `body_data`、`payload`），供外部 CRC/奇偶异或函数使用。
- 校验函数在**目标语言侧**写，比对 `stored_checksum`（§8.1 方式 C）。
- 惰性字段只在访问时才真正读取，校验不涉及的数据块不会被浪费地解析。

## 10. 两个示例的对照拆解

### 10.1 示例 1（`frameseq`，帧 + 事件）

- 顶层 `frames` 用 `repeat: eos` 循环读帧，直到文件结束。
- 帧头 `header` 用 `valid: eq: 0x1c1c2288` 做**运行时断言**；帧尾 `tail` 用 `contents` 匹配固定魔数 `[0xcc, 0x11, 0x88, 0x22]`。
- `events` 是子类型 `event`，用 `repeat: expr` 固定读 41 个事件（事件内 `timestamp`/`data_max`/`data_base` 均为简单整数）。
- `body_data` 用 `instances` + `pos: 0` 取整帧 522 字节——**注意 522 = 整帧总长减去 CRC 与帧尾等固定字段**，这是"把帧主体切出来做校验"的典型写法。

### 10.2 示例 2（`frameseq`，帧 + 未知块）

- 同样顶层 `repeat: eos`，但每帧不是单一类型，而是 `frame_and_unknown = frame + unknown` 的组合类型。
- `frame` 里全是定长整数字段（大量 `u2`/`s2` 电压电流、SiPM 通道量、`saa_judge_method`、`crc16`）。
- `unknown` 用 `repeat: expr` 读 78 字节未知数据——**"已知帧 + 未知块"的骨架**：已知字段用 `seq` 精确定义，尚未破解的区段用固定长度 `repeat: expr` 兜住，保证解析游标不错位。
- `body_data` 取 107 字节，与示例 1 同款"整帧原始字节"手法，只是帧长不同。

### 10.3 共同模式总结

1. **帧结构 = 魔数（`valid`/`contents` 校验）+ 定长字段（`seq`）+ 定长事件块（`repeat: expr`）+ 校验/尾字段**。
2. **帧主体用 `instances` 整块取出**，供 CRC 等外部校验逻辑复用。
3. **未知/未破解区段用 `repeat: expr` 定长兜底**，避免解析游标错位。

## 11. `ksc` 编译器与工具链

`ksc`（Kaitai Struct Compiler）是把 `.ksy` 编译成目标语言解析器的命令行工具——日记里"自动生成解析器"指的就是这一步（见 [kaitai_struct_compiler README](https://github.com/kaitai-io/kaitai_struct_compiler)）。

```bash
ksc -t python frameseq.ksy                                  # 生成 Python 解析器
java -jar kaitai-struct-compiler.jar -t python frameseq.ksy  # JAR 等价形式
```

常用选项：

- `-t <lang>` / `--target`：目标语言（`python`、`java`、`javascript`、`cpp_stl`、`csharp`、`go`、`ruby`、`php`、`perl`、`lua`、`nim` …）
- `-d <dir>` / `--outdir`：输出目录
- `--debug`：生成带调试信息的解析器
- `--import-path <dir>`：指定 `import` 搜索路径

生成物是"目标语言解析器代码 + 该语言的 runtime 库"：把文件字节交给解析器的 `read()`，就能得到按 `.ksy` 结构解析好的对象树。

> 与流水线的关系：`parse → validate → write` 中，`ksc` 只产出 `parse` 阶段的解析器；`validate`（CRC、奇偶异或）与 `write` 不在 KSY/ksc 范围内，需另外实现。

## 12. 解析产物：KaitaiStruct 对象（不是 dict）

> 这是 `validate` 落地的第一道坎——生成解析器读出来的**不是 Python dict**，而是 `KaitaiStruct` 子类对象。

### 12.1 产物长什么样

`ksc -t python` 为顶层 `meta.id`（如 `frameseq`）生成一个类 `Frameseq(KaitaiStruct)`，用法如下：

```python
from frameseq import Frameseq

data = Frameseq.from_file("data.hk")   # 或 Frameseq(KaitaiStream(open(...,'rb'))).read()
print(data.frames)                     # 字段名即属性：seq/types/instances 全在对象上
print(data.frames[0].header)           # repeat 字段是 list，子结构是嵌套对象
```

- 每个 `.ksy` 里的 `id` 都变成一个**属性**（`data.frames`、`data.frames[0].header`），`instances` 的字段（如 `body_data`）也以属性形式访问。
- 子结构（`type: frame`）是**嵌套的 `KaitaiStruct` 对象**，`repeat` 字段是这些对象的 **list**。
- 对象还带内部成员：`_io`（KaitaiStream 句柄）、`_root`（顶层对象引用）、`_parent`（父对象引用）——它们**不是普通数据**，含文件句柄与循环引用。
- `seq` 字段与 `instances` 字段**在对象上无法从外部区分**（都是 `obj.field`），区别只在内部机制（见 §9.1）。

### 12.2 为什么不能直接 `json.dumps`

`json.dumps(data)` 会失败：`_io` 是含文件句柄的流对象、`_root`/`_parent` 是循环引用，且自定义类没有 JSON 序列化器。

- 要落盘/传输/给前端展示，才需要**手动转 dict**（见 §12.4）；
- **校验阶段不要转 dict**，直接用对象（见 §12.3）。

### 12.3 校验：用原始对象，不要转 dict

- **直接读字段值**做校验：`frame.crc16` 是整数、`frame.header` 是整数，`valid` 断言失败的字段在解析时就会抛异常。
- **CRC 校验**要用**原始字节**：`frame.body_data` 是 `instances` 惰性取出的字节序列，把它喂给外部 CRC 函数，再与 `frame.crc16` 比对：

```python
for frame in data.frames:
    calc = crc16(frame.body_data)        # 外部 CRC 库，输入是原始字节
    if calc != frame.crc16:              # 字段值直接是 int，可直接比较
        raise ValueError(f"CRC mismatch: {calc:#x} != {frame.crc16:#x}")
```

- **奇偶/异或校验**同理：把 `frame.body_data` 逐字节异或累加出校验和，与协议字段比对。
- 关键点：`body_data` 这类 `instances` 字段正是为"取整段原始字节供校验"而生的（见 §9），校验时直接消费它，无需先转 dict。

### 12.4 什么时候才转 dict

只有**落盘（存 JSON）、跨系统传输、前端展示**时才需要手动转。推荐做法是**只转你需要的字段**，而不是盲目 `__dict__`：

```python
def to_dict(frame):
    return {
        "header": frame.header,
        "utc": frame.utc,
        "crc16": frame.crc16,
        "body_len": len(frame.body_data),
    }
```

- 想一键转完整 dict 可遍历 `data.__dict__` 并**跳过 `_io`/`_root`/`_parent`**，再递归处理嵌套对象与 list；或借助社区脚本（见 [Kaitai Struct dump to json](https://stackoverflow.com/questions/66649554/kaitai-struct-dump-to-json)）。
- 更省事：用 `ksc` 生成的 **Ruby / 自带可视化** 或 Web IDE 直接看对象树，Python 下则手动写 `to_dict`。
- 若字段含 `bytes`（如 `body_data`），JSON 需转成 base64 或十六进制字符串，不能直接 `json.dumps`。

> 结论：**校验用原始 KaitaiStruct 对象（尤其 `body_data` 字节 + 数值字段直接比对）；转 dict 只在需要落盘/传输/展示时做，且要手动、显式地转。**

## 相关

- 项目实战记录：生活/日记/2026-09-01 · 2026-09-02 · 2026-09-04 · 2026-09-05
- 项目待办：生活/日程/2026-09-06
- 官方用户指南：[doc.kaitai.io/user_guide.html](https://doc.kaitai.io/user_guide.html)
- 固定字节 `contents` 参考：[gzip 格式规范](https://formats.kaitai.io/gzip/)
