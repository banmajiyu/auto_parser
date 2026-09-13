"""Pipeline：串起 Parser -> Validator -> Writer。

数据流：raw_data --Parser--> parsed_data --Validator--> data --Writer--> JSON/CSV

CRC 校验配置在 conf.json 的**顶层 `CRC_ALGO`**（与 PARSER 条目完全无关）：
    每个算法条目给出 MODULE/FUNC/SIZE/INIT/BYTEORDER/**TAIL**/DROP_ON_FAIL，
    并用 `SUPPORT` 声明“该算法默认适用于哪些文件格式”（可按格式覆盖 TAIL 等参数）。

算法选择策略：
    1. 显式指定（`crc_algo=` 参数 / CLI `--crc-algo`）-> 用指定算法；
    2. 未指定 -> 按源文件后缀在各算法的 SUPPORT 中匹配，命中即默认使用；
    3. 都没命中 -> 跳过校验（`checked` 不增加）。

校验不依赖生成解析器的调试信息（.ksy 不写 ks-debug）；算法实现可插拔（`src/checks/`）。
"""

import os

from src.parser import Parser
from src.validator import Validator
from src.writer import Writer


class Pipeline():
    """一次解析任务的完整流水线。

    用法：
        result = Pipeline(parser_entry, src, des, output_type=["csv", "json"]).run()
        result == {
            "packet_len": int,     # 单包长度（0 = 变长包）
            "count": int,          # 解析出的数据包数量
            "unparsed": int,       # 定长切片中因帧头/帧尾/contents 校验失败被跳过的包数
            "valid": int,          # 通过校验、实际写出的记录数
            "dropped": int,        # 因 CRC 校验失败被丢弃的包数
            "checked": int,        # 实际参与 CRC 校验的包数（0 = 跳过）
            "trailing": int,       # 末尾未对齐字节数
            "paths": dict,         # {格式: 文件路径}；output_type 为空则不写文件
        }
    """

    def __init__(self, parser_entry: dict, src: str, des: str,
                 output_type: list | str | None = None,
                 crc_algo: str | None = None) -> None:
        self.parser_entry = parser_entry
        self.src = src
        self.des = des
        self.crc_algo = crc_algo    # 显式指定的 CRC 算法（None = 按源文件格式自动匹配）
        # 仅在“未传入”时默认 csv + json；空列表 [] 是有意义的“不写文件”，需保留
        self.output_type = output_type if output_type is not None else ["csv", "json"]

    def run(self) -> dict:
        """执行整条流水线，返回结果 dict。"""
        parser = Parser(self.parser_entry, self.src)

        # 1) 校验：用哪个算法/位置全部由 conf 顶层 CRC_ALGO（+ SUPPORT）决定，与 PARSER 解耦；
        #    这里只透传“显式指定”的算法，未指定时 Validator 按源文件格式自动匹配
        validator = Validator(parser, crc_algo=self.crc_algo)
        data = validator.process()

        # 2) 写出：output_type 为空（conf 配了 []）或无可写数据则只解析、不写文件
        paths = {}
        if self.output_type and data:
            stem = os.path.splitext(os.path.basename(self.src))[0]
            writer = Writer(data, self.des, stem, type=self.output_type)
            paths = writer.write()

        return {
            "packet_len": parser.packet_len,
            "count": len(parser.packets),
            "unparsed": parser.unparsed,
            "valid": len(data),
            "dropped": validator.dropped,
            "checked": validator.checked,
            "trailing": parser.trailing,
            "paths": paths,
        }