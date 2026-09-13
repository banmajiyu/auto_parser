import sys
import os
import importlib
import inspect
from kaitaistruct import KaitaiStream, BytesIO, KaitaiStruct

conf_route = r".\conf\conf.json"
parser_dir = r".\generated"

class Parser():
    """二进制数据通用解析类，调用解析器解析二进制流。

    用法：
        p = Parser(parser_entry, src)
        p.packets       # 解析出的原始数据包对象列表
        p.fields        # 字段名列表（取自第一个数据包）
        p.trailing      # 末尾未对齐字节数
        p.packet_len    # 单包长度（0 表示变长包，逐包解析）        p.unparsed      # 定长切片中因帧头/帧尾/contents 校验失败被跳过的包数        p.to_records()  # [{字段: 基础类型值}, ...]，供 CSV/JSON 输出
    """

    # ksy 里承载 CRC 校验参数的元数据实例前缀（crc_skip0/crc_tail/…，不写入输出记录）
    CRC_META_PREFIX = "crc_"

    def __init__(self, parser_entry, src) -> None:
        self.parser_entry = parser_entry
        self.src = src
        # 解析结果由 _parse 填充
        self.packets = []   # 解析出的原始数据包对象列表
        self.fields = []    # 字段名列表（取自第一个数据包）
        self.trailing = 0   # 末尾未对齐字节数
        self.unparsed = 0   # 定长切片中因校验失败（帧头/帧尾/contents）被跳过的包数
        self.raw_chunks = []  # 与 packets 一一对应的原始字节切片（供校验用）
        # PACKET_LEN<=0 表示变长包：逐包解析并按实际消耗字节推进
        self.packet_len = int(parser_entry.get("PACKET_LEN") or 0)
        self._parse()

    def _parse(self) -> list:
        """ 解析主函数 """
        with open(self.src, "rb") as f:
            data = f.read()

        packet_class = self._import_packet_class(self.parser_entry)
        # PACKET_LEN<=0 表示变长包：逐包解析并按实际消耗字节推进
        packet_len = int(self.parser_entry.get("PACKET_LEN") or 0)
    
        packets, trailing, raw_chunks = self._parse_packets(packet_class, data, packet_len)
        if not packets:
            hint = (f"（已跳过 {self.unparsed} 个校验失败的包）" if self.unparsed else "")
            raise RuntimeError(
                f"{self.src} 中没有可解析的 {packet_len} 字节数据包{hint}。"
                "请核对 PACKET_LEN 与文件版本是否匹配（例：HK 有 187B / 178B 两版、"
                "FT 有 grid / yingtian 两版）")
    
        fields = self._member_names(packets[0])
        self.packets = packets
        self.fields = fields
        self.trailing = trailing
        self.raw_chunks = raw_chunks
        return packets

    def to_records(self):
        """将解析结果转换为 [{字段: 基础类型值}, ...] 的列表。

        供 CSV/JSON 输出直接消费，调用方无需关心 Kaitai 对象结构。
        """
        return [
            {fld: self._to_primitive(getattr(pkt, fld)) for fld in self.fields}
            for pkt in self.packets
        ]

    def _import_packet_class(self, entry):
        """
        根据 conf 注册信息动态导入 Kaitai 生成的解析类。
        需要 conf.json 中该解析器配置了 MODULE（模块名）与 CLASS（类名）。
        """
        module_name = entry.get("MODULE")
        class_name = entry.get("CLASS")
        if not module_name or not class_name:
            raise RuntimeError(
                f"解析器 '{entry.get('NAME')}' 未配置 MODULE/CLASS，"
                "请先用 scripts/compile_ksy.py 生成 Kaitai 解析代码，"
                "并在 conf/conf.json 中补充对应字段。"
            )
        sys.path.insert(0, os.path.abspath(parser_dir))
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    def _parse_packets(self, packet_class, data, packet_len):
        """解析字节流为数据包列表，返回 (包列表, 末尾未对齐字节数, 原始切片列表)。

        - packet_len > 0: 按固定包长切片解析
        - packet_len <= 0: 变长包，逐包解析并按解析器实际消耗字节推进
        raw_chunks 与 packets 一一对应，供 Validator 做 CRC 等字节级校验。
        """
        packets = []
        raw_chunks = []
        pos = 0
        if packet_len > 0:
            while pos + packet_len <= len(data):
                chunk = data[pos:pos + packet_len]
                try:
                    packet = self._construct(packet_class, KaitaiStream(BytesIO(chunk)))
                except Exception:
                    # 单包解析失败（帧头/帧尾/contents 校验不过）：跳过该包并继续，
                    # 与“CRC 失败丢包”保持同一粒度，避免个别坏包/错位中断整个文件
                    self.unparsed += 1
                    pos += packet_len
                    continue
                packets.append(packet)
                raw_chunks.append(chunk)
                pos += packet_len
        else:
            while pos < len(data):
                try:
                    io = KaitaiStream(BytesIO(data[pos:]))
                    packet = self._construct(packet_class, io)
                    consumed = io.pos()
                    if consumed <= 0:
                        break
                    packets.append(packet)
                    raw_chunks.append(data[pos:pos + consumed])
                    pos += consumed
                except Exception:
                    break  # 剩余数据无法构成完整包
        return packets, len(data) - pos, raw_chunks

    @staticmethod
    def _construct(packet_class, io):
        """构造并完整读取一个数据包对象。

        兼容两种生成代码：
        - 普通模式：__init__ 内部已调用 _read()，字段就绪；
        - 调试模式（编译时 ksc --debug）：__init__ **不**调用 _read()，
          需显式补读一次。本项目不再要求调试信息，此处仅为兼容手工编译的产物。
        """
        packet = packet_class(io)
        if not any(not k.startswith("_") for k in vars(packet)):
            packet._read()
        return packet

    def _to_primitive(self, value):
        """将 Kaitai 解析结果转换为可 JSON 序列化的基础类型。

        - KaitaiStruct -> dict（seq 字段 + 惰性 instances，如 converted/body_data）
        - list/tuple    -> list
        - bytes         -> 十六进制字符串
        - 其它          -> 原值（int/float/str/IntEnum 等）
        """
        if isinstance(value, KaitaiStruct):
            return {
                k: self._to_primitive(getattr(value, k))
                for k in self._member_names(value)
            }
        if isinstance(value, (list, tuple)):
            return [self._to_primitive(item) for item in value]
        if isinstance(value, bytes):
            return value.hex()
        return value

    @staticmethod
    def _member_names(obj) -> list:
        """收集 Kaitai 对象上要输出的成员：seq 字段 + instances。

        - seq 字段：普通生成代码由公共属性给出，并剔除参数化类型的构造参数
          （如 scaled 的 scale/offset，用 __init__ 形参名识别）；
          若生成代码恰好带调试信息（编译时 ksc --debug），则改用 `_debug` 的键，
          排除 `_m_` 前缀的惰性缓存键。
        - instances：生成代码以 @property 实现（如 converted/body_data），
          不在 vars(obj) 中，需从类属性中收集；`crc_*` 开头的是 CRC 校验元数据
          （crc_skip0/crc_tail/…，供 Validator 使用），不写入输出记录。
        """
        debug = getattr(obj, "_debug", None)
        if debug:
            names = [k for k in debug.keys() if not k.startswith("_m_")]
        else:
            params = Parser._init_param_names(type(obj))
            names = [
                k for k in vars(obj)
                if not k.startswith("_") and k not in params
            ]

        for name in dir(type(obj)):
            if name.startswith("_") or name.startswith(Parser.CRC_META_PREFIX):
                continue
            if isinstance(getattr(type(obj), name, None), property) and name not in names:
                names.append(name)
        return names

    @staticmethod
    def _init_param_names(obj_cls) -> frozenset:
        """参数化类型（如 scaled）的构造参数名集合。

        生成代码没有调试信息时，vars(obj) 会把类型参数（scale/offset 等）
        与 seq 字段混在一起；用 __init__ 的形参名把前者排除，避免污染输出。
        """
        try:
            sig = inspect.signature(obj_cls.__init__)
        except (TypeError, ValueError):
            return frozenset()
        reserved = {"self", "_io", "_parent", "_root"}
        return frozenset(p.name for p in sig.parameters.values() if p.name not in reserved)