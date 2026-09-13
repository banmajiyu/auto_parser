"""Validator：解析结果的语义校验（CRC，算法可插拔）。

流水线位置：
    raw --Parser--> parsed --Validator--> data --Writer--> 文件

为什么 CRC 不写在 .ksy 里（见 `doc/kaitai struct说明.md` §8）：
    Kaitai Struct 是**纯声明式**解析器，语言中立，不认识目标语言的 CRC/哈希函数。
    `value: calc_crc(payload)` 这类写法不合法；CRC 属于"语义校验"，
    必须在应用层（本模块）完成，KSY 只负责把原始字节与字段值暴露出来。

CRC 校验的全部参数（算法、位置、初值、是否丢弃）都写在 conf.json 的**顶层 `CRC_ALGO`**
（ksy 不承担校验职责，生成解析器也不需要带调试信息）；`Validator(...)` 的同名参数只用于
在代码里临时覆盖（如测试、自定义函数），不写时均取 conf 里的值。

算法实现是**可插拔**的（每个算法一个文件放在 `src/checks/`），算法表也**不在代码里注册**，
而是写在 `conf/conf.json` 顶层 `CRC_ALGO` 数组（唯一真源）。**算法表与 PARSER 完全解耦**：

    "CRC_ALGO": [
        {"NAME": "crc16_ccitt", "MODULE": "src.checks.crc16_ccitt", "FUNC": "crc16_ccitt",
         "SIZE": 2, "INIT": "0x0000", "BYTEORDER": "big", "TAIL": 2,
         "SUPPORT": [{"TYPE": ".hk"}, {"TYPE": ".ft", "TAIL": 6}], "DESCRIPTION": "..."}
    ]

选择策略（不看 PARSER 里的任何字段）：
    1. 校验参数显式指定了算法（`crc_algo` / CLI `--crc-algo`）-> 直接用指定算法；
    2. 未指定 -> 按源文件后缀在**各算法的 SUPPORT 列表**里找“支持的格式”，命中即默认使用；
    3. 都没命中 -> 不做校验（跳过，`checked` 不增加）。
`TAIL` / `SIZE` / `INIT` / `BYTEORDER` / `DROP_ON_FAIL` 在算法条目里给默认值，
可在具体 SUPPORT 条目里按格式覆盖（如 `.ft` 的 `"TAIL": 6`；`"ENABLE": false` 则该格式不校验）。
* 参考文档见 `crc_reference.md`（CRC16 = CRC-16/XMODEM；CRC32 = CRC-32C，注意不是 zlib CRC-32）。

校验规则（与需求方给定的参考实现一致）：
    - CRC 字段（对象树中名字以 "crc" 开头的字段）起点 = 包尾往前 `TAIL` 字节、长度 `SIZE`；
    - provided = raw[包尾-TAIL : 包尾-TAIL+SIZE] 按 byteorder 转 int（存储值）；
    - computed = 所选算法 `FUNC(raw[:crc_start], init=INIT)`（计算值）；
    - 两者不等 -> 该包校验失败；默认**丢弃**该包并继续处理后续包；
    - 包内没有 crc 字段 / 未匹配到算法 -> 跳过校验（返回 None，不计入 checked）。

用法：
    from src.parser import Parser
    from src.validator import Validator, crc16_ccitt

    parser = Parser(parser_entry, src)
    records = Validator(parser).process()      # [{字段: 基础值}, ...]

    v = Validator(parser)
    v.process()
    v.dropped        # 被丢弃的包数
    v.checked        # 实际参与 CRC 校验的包数
"""

import importlib
import json
import os

from kaitaistruct import KaitaiStruct

from src.checks.crc16_ccitt import crc16_ccitt   # re-export，保持历史调用兼容

__all__ = ["Validator", "crc16_ccitt", "load_algorithms", "algorithms_from_conf",
           "get_algorithm", "list_algorithms", "resolve_policy"]

# 算法表所在配置文件（与 src/parser.py 的 conf_route 保持一致；模块级变量便于测试时替换）
conf_route = r".\conf\conf.json"


def _as_int(value, default: int = 0) -> int:
    """把 conf 里的数值统一成 int；支持 int、十进制字符串、"0x.." 十六进制字符串。"""
    if value is None:
        return default
    if isinstance(value, str):
        return int(value, 0)
    return int(value)


def _as_bool(value, default: bool = True) -> bool:
    """把 conf 里的布尔值统一成 bool（支持 true/false、"0"/"1"、"yes"/"no"）。"""
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() not in ("false", "0", "no", "off", "")
    return bool(value)


_POLICY_KEYS = ("NAME", "MODULE", "FUNC_NAME", "FUNC",
                "SIZE", "INIT", "BYTEORDER", "TAIL", "DROP_ON_FAIL")


def _defaults(item: dict) -> dict:
    """算法条目本身的默认校验参数（不含 SUPPORT）。"""
    return {
        "SIZE": int(item.get("SIZE", 2)),
        "INIT": _as_int(item.get("INIT"), 0),
        "BYTEORDER": item.get("BYTEORDER", "big"),
        "TAIL": int(item.get("TAIL", 2)),
        "DROP_ON_FAIL": _as_bool(item.get("DROP_ON_FAIL"), True),
    }


def _support_policies(item: dict, base: dict) -> tuple:
    """把 SUPPORT 规范成“每个格式一条完整策略”。

    SUPPORT 元素可以是格式字符串（".hk"）、或对象：
        {"TYPE": ".ft", "TAIL": 6}            // 覆盖该格式的默认参数
        {"TYPE": [".iv", ".vbr"]}            // 一条涵盖多个格式
        {"TYPE": ".ft", "ENABLE": false}      // 该格式不校验（等效于不写）
    未写 SUPPORT / 未命中任何格式 -> 该格式不做 CRC 校验。
    """
    policies = []
    for raw in item.get("SUPPORT") or []:
        spec = {"TYPE": raw} if isinstance(raw, str) else dict(raw or {})
        types = spec.get("TYPE")
        types = [types] if isinstance(types, str) else list(types or [])
        if not types or not _as_bool(spec.get("ENABLE"), True):
            continue
        policy = dict(base)
        if spec.get("SIZE") is not None:
            policy["SIZE"] = int(spec["SIZE"])
        if spec.get("INIT") is not None:
            policy["INIT"] = _as_int(spec["INIT"], 0)
        if spec.get("BYTEORDER"):
            policy["BYTEORDER"] = spec["BYTEORDER"]
        if spec.get("TAIL") is not None:
            policy["TAIL"] = int(spec["TAIL"])
        if spec.get("DROP_ON_FAIL") is not None:
            policy["DROP_ON_FAIL"] = _as_bool(spec["DROP_ON_FAIL"], True)
        for fmt in types:
            policies.append({**policy, "TYPE": fmt})
    return tuple(policies)


def algorithms_from_conf(configure: dict) -> dict:
    """把已加载的 conf（dict）转成算法表：{NAME: 归一化条目}。

    条目字段：NAME/MODULE/FUNC/FUNC_NAME/SIZE/INIT/BYTEORDER/TAIL/DROP_ON_FAIL/SUPPORT/DESCRIPTION；
    `FUNC` 已按 MODULE+FUNC 动态导入为可调用对象，`SUPPORT` 已展开为逐格式的完整策略。
    """
    table = {}
    for item in configure.get("CRC_ALGO") or []:
        name = item.get("NAME")
        if not name:
            raise RuntimeError(f"conf 的 CRC_ALGO 条目缺少 NAME：{item}")
        module_name, func_name = item.get("MODULE"), item.get("FUNC")
        if not module_name or not func_name:
            raise RuntimeError(f"CRC 算法 '{name}' 未配置 MODULE/FUNC")
        module = importlib.import_module(module_name)
        # 基础策略 = 算法身份（NAME/MODULE/FUNC...）+ 默认参数；SUPPORT 里每条都继承它
        base = {
            "NAME": name,
            "MODULE": module_name,
            "FUNC_NAME": func_name,
            "FUNC": getattr(module, func_name),
            **_defaults(item),
        }
        table[name] = {
            **base,
            "SUPPORT": _support_policies(item, base),
            "DESCRIPTION": item.get("DESCRIPTION", ""),
        }
    return table


def load_algorithms(path: str | None = None) -> dict:
    """读 conf.json，返回 {NAME: 归一化算法条目}（见 algorithms_from_conf）。"""
    with open(path or conf_route, "r", encoding="utf-8") as f:
        configure = json.load(f)
    return algorithms_from_conf(configure)


def get_algorithm(name: str, path: str | None = None) -> dict:
    """按名字从 conf 的 CRC_ALGO 表查算法；未配置时抛 KeyError 并列出可选值。"""
    table = load_algorithms(path)
    try:
        return table[name]
    except KeyError:
        available = ", ".join(sorted(table)) or "(空)"
        raise KeyError(f"conf 的 CRC_ALGO 中未找到算法 '{name}'，可选：{available}") from None


def list_algorithms(path: str | None = None) -> tuple:
    """conf 中已声明的算法名（排序后）。"""
    return tuple(sorted(load_algorithms(path)))


def resolve_policy(fmt: str | None, crc_algo: str | None = None,
                   path: str | None = None) -> dict | None:
    """选出一条完整校验策略（含 FUNC/SIZE/INIT/BYTEORDER/TAIL/DROP_ON_FAIL/TYPE/NAME）。

    参数：
        fmt      : 源文件格式（如 ".hk"）
        crc_algo : 显式指定的算法名（conf CRC_ALGO 的 NAME）；None = 按 fmt 在 SUPPORT 里匹配
    返回 None 表示“不做校验”（未显式指定且没有任何算法的 SUPPORT 命中该格式）。
    """
    table = load_algorithms(path)

    if crc_algo:
        algo = table.get(crc_algo)
        if algo is None:
            available = ", ".join(sorted(table)) or "(空)"
            raise KeyError(f"conf 的 CRC_ALGO 中未找到算法 '{crc_algo}'，可选：{available}")
        for policy in algo["SUPPORT"]:
            if policy["TYPE"] == fmt:
                return policy
        # 显式指定算法：即使该格式未声明 SUPPORT，也按算法默认参数执行
        policy = {k: algo[k] for k in _POLICY_KEYS}
        policy["TYPE"] = fmt
        return policy

    for algo in table.values():
        for policy in algo["SUPPORT"]:
            if policy["TYPE"] == fmt:
                return policy
    return None


class Validator():
    """对 Parser 的解析结果做语义校验，并产出可写出的记录列表。

    用法：
        v = Validator(parser, crc=True, drop_on_fail=True)
        data = v.process()   # 通过校验的记录；校验失败的包被丢弃
        v.dropped            # 丢弃数量
        v.checked            # 参与校验的包数量（无 crc 字段时为 0）
    """

    CRC_PREFIX = "crc"          # 字段名前缀：以它开头的字段视为 CRC 字段

    # ksy `instances` 中的 CRC 元数据实例名 -> 内部策略键
    # （写在“带 crc 字段的类型”的 instances 里，可选；声明后优先于构造参数/conf）
    _KSY_META_KEYS = {
        "crc_skip0": "SKIP0",      # CRC 计算时从包首跳过的字节数
        "crc_skip1": "SKIP1",      # CRC 计算时从结尾向前排除的字节数
        "crc_tail": "TAIL",        # CRC 字段起点距包尾的字节数
        "crc_bytes": "SIZE",       # CRC 字段字节数（别名 crc_size）
        "crc_size": "SIZE",
        "crc_init": "INIT",        # 初值
        "crc_byteorder": "BYTEORDER",
        "crc_algo": "ALGO",        # 算法名（conf CRC_ALGO 的 NAME）
    }

    def __init__(self, parser, crc: bool = True, crc_func=None,
                 crc_init=None, drop_on_fail=None,
                 byteorder: str | None = None, crc_tail=None,
                 crc_size=None, crc_algo: str | None = None,
                 fmt: str | None = None, conf_path: str | None = None) -> None:
        """
        parser        : 已解析完成的 Parser 实例（用于取源文件后缀）
        crc           : 总开关（False = 完全不校验）
        crc_algo      : 显式指定算法（conf CRC_ALGO 的 NAME）；None = 按源文件格式自动匹配 SUPPORT
        crc_func      : 自定义 CRC 函数，签名 (data, init=0) -> int；显式给出时优先于 conf
        crc_init      : CRC 初值（int 或 "0x.." 字符串）；None = 取策略默认
        drop_on_fail  : 校验失败是否丢弃该包；None = 取策略默认（true）
        byteorder     : 读取存储 CRC 时的字节序（"big"/"little"）；None = 取策略默认
        crc_tail      : CRC 字段起点距包尾的字节数（含 CRC 自身及其后的字节）；None = 取策略默认
                        例：CRC 恰好是包内最后一个字段 -> 2；
                            后面还有 4 字节帧尾（如 FT/ES 事件块） -> 6；WF = 8
        crc_size      : CRC 字段字节数；None = 取策略默认
        fmt           : 源文件格式（如 ".hk"）；None = 从 parser.src 的后缀推断
        conf_path     : 算法表所在 conf.json 路径（默认 .\\conf\\conf.json）
        """
        fmt = fmt if fmt is not None else os.path.splitext(getattr(parser, "src", "") or "")[1]

        # 显式指定（算法名 / 自定义函数）时不看格式直接取策略；否则按源文件格式在 SUPPORT 中匹配
        if not crc:
            policy = None
        else:
            policy = resolve_policy(fmt, crc_algo, conf_path)

        self.parser = parser
        self.fmt = fmt
        self.crc = crc
        self.crc_policy = policy
        self.conf_path = conf_path
        self.crc_algo_explicit = bool(crc_algo)   # 显式指定的算法优先于 ksy 声明
        self.crc_func_explicit = crc_func is not None   # 调用方自带的函数优先于 ksy 声明
        self.crc_algo = policy["NAME"] if policy else None
        self.crc_func = crc_func if crc_func is not None else (
            policy["FUNC"] if policy else None)
        self.crc_init = _as_int(crc_init) if crc_init is not None else (
            policy["INIT"] if policy else 0)
        self.crc_size = int(crc_size) if crc_size is not None else (policy["SIZE"] if policy else 2)
        self.crc_tail = int(crc_tail) if crc_tail is not None else (policy["TAIL"] if policy else 2)
        self.byteorder = byteorder or (policy["BYTEORDER"] if policy else "big")
        self.drop_on_fail = (_as_bool(drop_on_fail) if drop_on_fail is not None
                             else (policy["DROP_ON_FAIL"] if policy else True))

        self.dropped = 0        # 被丢弃的包数
        self.checked = 0        # 实际参与 CRC 校验的包数

    # ------------------------------------------------------------------ #
    # 对外主入口
    # ------------------------------------------------------------------ #
    def process(self) -> list:
        """校验所有包，返回通过校验的记录列表（[{字段: 基础值}, ...]）。"""
        self.dropped = 0
        self.checked = 0

        records = []
        for pkt, raw in zip(self.parser.packets, self.parser.raw_chunks):
            ok = self._check_crc(pkt, raw)
            if ok is not None:
                self.checked += 1
            if ok is False and self.drop_on_fail:
                self.dropped += 1
                continue
            records.append(self._to_record(pkt))
        return records

    # ------------------------------------------------------------------ #
    # 内部实现
    # ------------------------------------------------------------------ #
    def _to_record(self, pkt) -> dict:
        """把单个 Kaitai 对象转成 {字段: 基础值}（复用 Parser 的转换逻辑）。"""
        return {
            fld: self.parser._to_primitive(getattr(pkt, fld))
            for fld in self.parser.fields
        }

    def _check_crc(self, pkt, raw: bytes):
        """校验单个包。

        参数优先级：ksy `instances` 里声明的 CRC 元数据 > 构造参数/conf；
        例外：**算法**以显式指定（`crc_func` / `crc_algo` / CLI `--crc-algo`）为先，
        其次才是 ksy 的 `crc_algo`，最后是 conf 的 SUPPORT 匹配结果。

        返回：
            True  -> 校验通过
            False -> 校验失败（含参数越界，视为不合法）
            None  -> 跳过（未启用 / 无 crc 字段也无 ksy 元数据 / 无可用算法）
        """
        if not self.crc:
            return None

        meta = self._ksy_crc_meta(pkt)
        if not meta and not self._has_crc_field(pkt):
            return None

        # --- 算法：显式指定 > ksy 声明 > conf 匹配结果 ---
        if self.crc_algo_explicit or self.crc_func_explicit:
            func = self.crc_func
        elif meta.get("ALGO"):
            func = get_algorithm(str(meta["ALGO"]), self.conf_path)["FUNC"]
        else:
            func = self.crc_func
        if func is None:
            return None

        # --- 其余参数：ksy 元数据优先 ---
        tail = int(meta.get("TAIL", self.crc_tail))
        size = int(meta.get("SIZE", self.crc_size))
        init = _as_int(meta.get("INIT"), self.crc_init)
        skip0 = int(meta.get("SKIP0", 0))
        skip1 = int(meta.get("SKIP1", 0))
        byteorder = meta.get("BYTEORDER", self.byteorder)
        byteorder = "little" if str(byteorder).lower() == "little" else "big"

        crc_start = len(raw) - tail          # CRC 字段起点
        crc_end = crc_start + size           # CRC 字段终点
        cover_end = crc_start - skip1        # 参与计算区间的终点
        if skip0 < 0 or skip1 < 0 or crc_start < 0 or crc_end > len(raw) or cover_end < skip0:
            return False

        provided = int.from_bytes(raw[crc_start:crc_end], byteorder)
        computed = func(bytes(raw[skip0:cover_end]), init=init)
        return provided == computed

    def _ksy_crc_meta(self, root) -> dict:
        """读 ksy 在 `instances` 里声明的 CRC 元数据（没写则返回空 dict）。

        见 `_KSY_META_KEYS`；只读公共成员（属性/字段），与 `_has_crc_field` 一样
        遍历对象树并用 id() 去重。
        """
        meta = {}
        stack = [root]
        seen = set()
        while stack:
            cur = stack.pop()
            if id(cur) in seen:
                continue
            seen.add(id(cur))

            for name, key in self._KSY_META_KEYS.items():
                if key in meta:
                    continue
                try:
                    value = getattr(cur, name)
                except Exception:            # 属性不存在 / 求值失败都当作未声明
                    continue
                if value is not None:
                    meta[key] = value

            for value in vars(cur).values():
                if isinstance(value, KaitaiStruct):
                    stack.append(value)
                elif isinstance(value, (list, tuple)):
                    stack.extend(v for v in value if isinstance(v, KaitaiStruct))
        return meta

    def _has_crc_field(self, root) -> bool:
        """对象树中是否存在名字以 "crc" 开头的字段。

        只做"有没有 CRC"的判断，定位则完全交给 crc_tail/crc_size 参数；
        因此不依赖生成解析器的调试信息（_debug）。对象树通过公共属性遍历，
        跳过 `_io/_root/_parent/_debug` 等内部成员，并以 id() 去重避免循环引用。
        """
        stack = [root]
        seen = set()
        while stack:
            cur = stack.pop()
            if id(cur) in seen:
                continue
            seen.add(id(cur))

            for name, value in vars(cur).items():
                if name.startswith("_"):
                    continue
                if name.lower().startswith(self.CRC_PREFIX):
                    return True
                if isinstance(value, KaitaiStruct):
                    stack.append(value)
                elif isinstance(value, (list, tuple)):
                    stack.extend(v for v in value if isinstance(v, KaitaiStruct))
        return False
