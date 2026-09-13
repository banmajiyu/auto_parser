import csv
import json
import os


class Writer():
    """把“可落盘”的数据(list[dict])写出为 JSON / CSV / Parquet。

    处于流水线末段：raw --Parser--> parsed --Validator--> data --Writer--> 文件。
    Writer 只关心 data（每包一条 dict、字段一致），不感知 Parser/Validator。

    用法：
        w = Writer(data, des, stem, type=["csv", "json", "parquet"])
        paths = w.write()   # 返回 {格式: 文件路径}
    """

    SUPPORTED = ("csv", "json", "parquet")   # 支持的输出格式
    SUFFIX = "_packets"            # 输出文件名固定后缀（沿用历史命名）

    def __init__(self, data: list, des: str, stem: str,
                 type: list | tuple | str = ("csv", "json")) -> None:
        if not data:
            raise ValueError("Writer: 无可写数据（data 为空），已跳过输出。")

        self.type = self._normalize_type(type)
        if not self.type:
            raise ValueError("Writer: 输出格式列表为空，请配置 conf 的 OUTPUT_TYPE。")

        self.data = data
        self.des = des
        self.stem = stem
        # CSV 列顺序取自第一条记录（各包字段一致）
        self.fields = list(data[0].keys())

    @staticmethod
    def _normalize_type(type) -> list:
        """把 str / list 统一成去重且保序的格式列表，并校验合法性。"""
        if isinstance(type, str):
            type = [t.strip() for t in type.split(",") if t.strip()]
        invalid = [t for t in type if t not in Writer.SUPPORTED]
        if invalid:
            raise ValueError(
                f"Writer: 不支持的输出格式 {invalid}，可选 {Writer.SUPPORTED}"
            )
        return list(dict.fromkeys(type))

    def write(self) -> dict:
        """按 self.type 写出对应格式，返回 {格式: 文件路径}。"""
        os.makedirs(self.des, exist_ok=True)
        paths = {}
        if "csv" in self.type:
            paths["csv"] = self._write_csv()
        if "json" in self.type:
            paths["json"] = self._write_json()
        if "parquet" in self.type:
            paths["parquet"] = self._write_parquet()
        return paths

    def _write_csv(self) -> str:
        """data -> <stem>_packets.csv（utf-8-sig，Excel 友好），返回路径。"""
        path = os.path.join(self.des, f"{self.stem}{self.SUFFIX}.csv")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(self.fields)
            for rec in self.data:
                writer.writerow([rec[fld] for fld in self.fields])
        return path

    def _write_json(self) -> str:
        """data -> <stem>_packets.json，返回路径。"""
        path = os.path.join(self.des, f"{self.stem}{self.SUFFIX}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        return path

    def _write_parquet(self) -> str:
        """data -> <stem>_packets.parquet（列式存储），返回路径。

        依赖 pyarrow：Table.from_pylist 自动推断 schema，支持嵌套 dict/list。
        pyarrow 未安装时抛出带安装提示的 ImportError。
        """
        path = os.path.join(self.des, f"{self.stem}{self.SUFFIX}.parquet")
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError as exc:
            raise ImportError(
                "Writer: 输出 parquet 需要安装 pyarrow（pip install pyarrow）。"
            ) from exc

        table = pa.Table.from_pylist(self.data)
        pq.write_table(table, path)
        return path