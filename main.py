import argparse
import json
import os
import sys
from tabulate import tabulate

from src.pipeline import Pipeline
from src.validator import algorithms_from_conf, load_algorithms, resolve_policy
from src.writer import Writer

# 支持格式的唯一真源：Writer.SUPPORTED（与代码能力一致，避免文案漂移）
SUPPORTED = ", ".join(Writer.SUPPORTED)


def build_guidance() -> str:
    """帮助文本：输出格式与 CRC 算法清单均取自唯一真源（Writer.SUPPORTED / conf 的 CRC_ALGO）。"""
    try:
        lines = []
        for name, algo in load_algorithms().items():
            types = " ".join(p["TYPE"] for p in algo["SUPPORT"]) or "(未声明 SUPPORT)"
            lines.append(f"    {name}  ->  {types}")
        crc_supported = "\n".join(lines) or "    (conf 未配置)"
    except Exception as e:                      # conf 缺失/损坏时不阻断查看帮助
        crc_supported = f"    (读取 conf 失败: {e})"

    return f"""
AUTO PARSER GUIDANCE

支持的输出格式：
    {SUPPORTED}

支持的 CRC 算法（conf.json 顶层 CRC_ALGO，-> 后为该算法默认适用的文件格式）：
{crc_supported}

参数：
    -s, --src         待解析文件的路径
    -d, --des         解析产物放置的路径
    --out-type        覆盖 conf OUTPUT_TYPE（逗号分隔，从上方“支持的输出格式”中选）
    --crc-algo        显式指定 CRC 算法（conf CRC_ALGO 的 NAME）；默认按源文件格式自动匹配
    -h, --help        帮助
    -c, --conf        查看配置文件

说明：
    conf/conf.json 的 OUTPUT_TYPE（数组）控制【默认】输出哪些格式；
    置空 [] 则本次只解析、不写文件；也可用 --out-type 临时覆盖。
    未在上方清单中的格式不受支持，程序会直接报错。
    CRC 是否校验/用哪个算法与 PARSER 无关：按源文件后缀在 CRC_ALGO 的 SUPPORT 中匹配，
    匹配不到则不校验；用 --crc-algo 可强制指定算法。
"""

conf_route = r".\conf\conf.json"

# 兼容 Windows 控制台 cp1252 及输出重定向场景，避免中文打印报 UnicodeEncodeError
for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if callable(_reconfigure):
        try:
            _reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

def run(parser_entry, src, des, fmt, out_type, crc_algo=None) -> dict:
    """打印参数表并驱动 Parser->Validator->Writer 流水线，返回结果 dict。"""
    # 展示本次实际会用到的算法：显式指定优先，否则按源文件格式在 SUPPORT 中匹配
    try:
        policy = resolve_policy(fmt, crc_algo)
        crc_desc = policy["NAME"] if policy else "(格式未匹配 → 不校验)"
    except Exception as e:
        crc_desc = f"(错误: {e})"

    print("开始解析...\n参数列表:")
    para = [
        ["解析器", parser_entry["NAME"]],
        ["源文件地址", src],
        ["输出地址", des],
        ["文件格式", fmt],
        ["输出格式", ",".join(out_type) if out_type else "无(仅解析)"],
        ["CRC 算法", crc_desc],
    ]
    print(tabulate(para, tablefmt="simple"))

    # 解析 / 校验 / 写出 全部收敛到 src/pipeline.py
    return Pipeline(parser_entry, src, des, out_type, crc_algo=crc_algo).run()

def main():
    # 通过命令行指定关键路径
    arg_parser = argparse.ArgumentParser(add_help=False)
    arg_parser.add_argument('-s', '--src', type=str, default=r".\test\sample.hk")
    arg_parser.add_argument('-d', '--des', type=str, default=r".\out")
    arg_parser.add_argument('--out-type', type=str, default=None,
                            help=f'覆盖 conf OUTPUT_TYPE（逗号分隔，支持：{SUPPORTED}）')
    arg_parser.add_argument('--crc-algo', type=str, default=None,
                            help='显式指定 CRC 算法（conf CRC_ALGO 的 NAME）；默认按源文件格式自动匹配')
    arg_parser.add_argument('-h', '--help', action='store_true')
    arg_parser.add_argument('-c', '--conf', action='store_true', help='查看配置表')
    args = arg_parser.parse_args()

    if args.help:
        print(build_guidance())
        return

    if args.conf:
        with open(r'.\conf\conf.json', encoding='utf-8') as conf:
            for line in conf:
                print(line)
        return

    source, destination = args.src, args.des
    file_extension = os.path.splitext(os.path.basename(source))[1]

    with open(conf_route, 'r', encoding='utf-8') as conf:
        configure = json.load(conf)
        parsers = configure['PARSER']

    # 输出格式：默认取 conf.json 的 OUTPUT_TYPE（数组）；CLI --out-type 可覆盖
    if args.out_type:
        out_type = [t.strip() for t in args.out_type.split(',') if t.strip()]
    else:
        out_type = list(configure.get('OUTPUT_TYPE') or [])

    # 提前校验格式，避免解析完大文件才在写出阶段报错
    unsupported = [t for t in out_type if t not in Writer.SUPPORTED]
    if unsupported:
        raise RuntimeError(
            f"不支持的输出格式：{unsupported}；支持：{Writer.SUPPORTED}"
        )

    # 按扩展名匹配解析器（conf 中 TYPE 形如 ".hk"）
    collected = [p for p in parsers if p['TYPE'] == file_extension]
    if not collected:
        raise RuntimeError(f"{source} 未支持的文件格式")

    if len(collected) == 1:
        entry = collected[0]
    else:
        print(f"有多个匹配到的解析器（共{len(collected)}个），请键入相应序号以选择（输入-1以退出程序）：\n")
        info = [["序号", "名称", "描述", "版本"]]
        for i, p in enumerate(collected):
            info.append([f"{i}", p['NAME'], p['DESCRIPTION'], p['VERSION']])
        print(tabulate(info, headers="firstrow", tablefmt="fancy_grid"))

        while True:
            try:
                idx = int(input(">>> "))
                if idx == -1:
                    return
                if not 0 <= idx < len(collected):
                    raise ValueError("序号超出范围")
            except Exception as e:
                print(e)
            else:
                break
        entry = collected[idx]

    # CRC 算法：--crc-algo 显式指定时必须存在于 conf 的 CRC_ALGO 表（不指定则按源文件格式自动匹配）
    algos = algorithms_from_conf(configure)
    if args.crc_algo and args.crc_algo not in algos:
        raise RuntimeError(
            f"--crc-algo '{args.crc_algo}' 不在 conf 的 CRC_ALGO 表中；"
            f"可选：{', '.join(sorted(algos)) or '(空)'}"
        )

    result = run(entry, source, destination, file_extension, out_type, args.crc_algo)

    size_desc = (
        f"每包 {result['packet_len']} 字节"
        if result['packet_len'] > 0
        else "变长包(逐包)"
    )
    print(f"共解析 {result['count']} 个数据包（{size_desc}），"
          f"末尾剩余 {result['trailing']} 字节未对齐")
    if result.get('unparsed'):
        print(f"⚠ 另有 {result['unparsed']} 个包因帧头/帧尾/内容校验失败被跳过"
              "（常见原因：文件是另一版本，或 PACKET_LEN 与文件不符）")
    if result.get('checked'):
        print(f"CRC 校验：通过 {result['valid']} 个，丢弃 {result['dropped']} 个")
    if result['paths']:
        print("输出文件:")
        for path in result['paths'].values():
            print(f"  {path}")
    print("解析完成")


if __name__ == "__main__":
    main()