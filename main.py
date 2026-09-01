import argparse
import csv
import importlib
import json
import os
import sys
from tabulate import tabulate
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO

guidance = """
AUTO PARSER GUIDANCE

参数：
    --src   待解析文件的路径
    --des   解析产物放置的路径
"""

conf_route = r".\conf\conf.json"
parser_dir = r".\generated"

# 兼容 Windows 控制台 cp1252 及输出重定向场景，避免中文打印报 UnicodeEncodeError
for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if callable(_reconfigure):
        try:
            _reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def _to_primitive(value):
    """将 Kaitai 解析结果转换为可 JSON 序列化的基础类型。"""
    if isinstance(value, KaitaiStruct):
        return {
            k: _to_primitive(getattr(value, k))
            for k in vars(value)
            if not k.startswith("_")
        }
    if isinstance(value, (list, tuple)):
        return [_to_primitive(item) for item in value]
    if isinstance(value, bytes):
        return value.hex()
    return value


def import_packet_class(entry):
    """根据 conf 注册信息动态导入 Kaitai 生成的解析类。

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


def parse_packets(packet_class, data, packet_len):
    """解析字节流为数据包列表，返回 (包列表, 末尾未对齐字节数)。

    - packet_len > 0: 按固定包长切片解析
    - packet_len <= 0: 变长包，逐包解析并按解析器实际消耗字节推进
    """
    packets = []
    pos = 0
    if packet_len > 0:
        while pos + packet_len <= len(data):
            chunk = data[pos:pos + packet_len]
            packet = packet_class(KaitaiStream(BytesIO(chunk)))
            packets.append(packet)
            pos += packet_len
    else:
        while pos < len(data):
            try:
                io = KaitaiStream(BytesIO(data[pos:]))
                packet = packet_class(io)
                consumed = io.pos()
                if consumed <= 0:
                    break
                packets.append(packet)
                pos += consumed
            except Exception:
                break  # 剩余数据无法构成完整包
    return packets, len(data) - pos


def write_outputs(packets, fields, src, des):
    """将解析结果输出为 CSV 与 JSON 两个文件，返回 (csv_path, json_path)。"""
    os.makedirs(des, exist_ok=True)
    file_name = os.path.splitext(os.path.basename(src))[0]
    base = os.path.join(des, file_name)

    csv_path = base + "_packets.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for pkt in packets:
            writer.writerow([_to_primitive(getattr(pkt, fld)) for fld in fields])

    json_path = base + "_packets.json"
    payload = [
        {fld: _to_primitive(getattr(pkt, fld)) for fld in fields}
        for pkt in packets
    ]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return csv_path, json_path

def parse(parser_entry, src, des, fmt):
    """ 解析主函数 """
    print("开始解析...\n参数列表:")
    para = [
        ["解析器", parser_entry["NAME"]],
        ["源文件地址", src],
        ["输出地址", des],
        ["文件格式", fmt],
    ]
    print(tabulate(para, tablefmt="simple"))

    with open(src, "rb") as f:
        data = f.read()

    packet_class = import_packet_class(parser_entry)
    # PACKET_LEN<=0 表示变长包：逐包解析并按实际消耗字节推进
    packet_len = int(parser_entry.get("PACKET_LEN") or 0)

    packets, trailing = parse_packets(packet_class, data, packet_len)
    if not packets:
        raise RuntimeError(f"{src} 中没有完整的 {packet_len} 字节数据包")

    fields = [k for k in vars(packets[0]) if not k.startswith("_")]
    csv_path, json_path = write_outputs(packets, fields, src, des)

    size_desc = f"每包 {packet_len} 字节" if packet_len > 0 else "变长包(逐包)"
    print(f"共解析 {len(packets)} 个数据包（{size_desc}），"
          f"末尾剩余 {trailing} 字节未对齐")
    print(f"输出文件:\n  {csv_path}\n  {json_path}")
    print("解析完成")

if __name__ == "__main__":

    # 通过命令行指定关键路径
    parser = argparse.ArgumentParser()
    parser.add_argument('--src', type = str, default = r".\in\sample.hk")
    parser.add_argument('--des', type = str, default = r".\out")

    args = parser.parse_args()

    source, destination = args.src, args.des

    full_name = os.path.basename(source)
    file_name, file_extension = os.path.splitext(full_name)

    #print(f"{source}, {destination}, {file_name, file_extension}")

    with open(conf_route, 'r', encoding='utf-8') as conf:
        # 从配置文件中检索相关解析器
        configure = json.load(conf)
        parsers = configure['PARSER']

        collected_parsers = [parser for parser in parsers if parser['TYPE'] == file_extension]

        if not collected_parsers:
            raise RuntimeError(f"{source} 未支持的文件格式")
        elif len(collected_parsers) == 1:
            parse(collected_parsers.pop(), source, destination, file_extension)
        else:
            print(f"有多个匹配到的解析器（共{len(collected_parsers)}个），请键入相应序号以选择：\n")
            info = [["序号", "名称", "描述", "版本"]]

            for i, parser in enumerate(collected_parsers):
                info.append([
                    f"{i}",
                    parser['NAME'],
                    parser['DESCRIPTION'],
                    parser['VERSION']
                ])
            print(tabulate(info, headers = "firstrow", tablefmt = "fancy_grid"))

            idx = None

            while True:
                try:
                    idx = int(input(">>> "))
                    if idx < 0 or idx > len(collected_parsers):
                        raise ValueError(f"索引超出范围")

                except Exception as e:
                    print(e)

                else:
                    break

            parse(collected_parsers[idx], source, destination, file_extension)