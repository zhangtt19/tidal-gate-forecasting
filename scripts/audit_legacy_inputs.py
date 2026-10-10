"""Compare archived training inputs with dated spreadsheet rows. Read-only sources."""

import argparse, json
from pathlib import Path
import numpy as np
import xlrd


def audit(source):
    findings = []
    for year in [2003, 2006]:
        for gate in ["斗龙", "黄沙", "射阳", "新洋"]:
            base = source / "5-转英文-Water/修改意见" / str(year) / f"{year}-{gate}"
            xls = base / f"{year}-{gate}.xls"
            dat = base / f"{gate} - BCDEFG.dat"
            b = xlrd.open_workbook(xls)
            s = next(s for s in b.sheets() if "粘贴为数值" in s.name)
            text = dat.read_text(encoding="gb18030").splitlines()
            matrix = []
            for line in text[3:]:
                try:
                    values = [float(v) for v in line.split()]
                    if len(values) == 7:
                        matrix.append(values)
                except ValueError:
                    pass
            a = np.array(matrix)
            table = []
            for row in range(1, s.nrows):
                values = s.row_values(row)
                if all(isinstance(v, (int, float)) for v in values[1:8]):
                    table.append(values[1:8])
            t = np.array(table)
            equal = a.shape == t.shape and np.allclose(a, t, rtol=1e-7, atol=1e-7)
            calc = next(s for s in b.sheets() if s.name.endswith("-计算"))
            checks = []
            for i in range(2, calc.nrows):
                prev, cur = calc.row_values(i - 1), calc.row_values(i)
                try:
                    dt = cur[0] - prev[0]
                    expected_q = (cur[8] - prev[8]) / dt
                    expected_head = ((cur[1] - cur[2]) - (prev[1] - prev[2])) / dt
                    head_sum = ((cur[1] - cur[2]) + (prev[1] - prev[2])) / dt
                    if dt > 0 and all(
                        np.isfinite(v)
                        for v in [expected_q, expected_head, cur[5], cur[6]]
                    ):
                        checks.append(
                            [
                                np.isclose(cur[6], expected_q),
                                np.isclose(cur[5], expected_head),
                                np.isclose(cur[5], head_sum),
                            ]
                        )
                except (TypeError, ZeroDivisionError):
                    pass
            c = np.array(checks)
            findings.append(
                {
                    "year": year,
                    "gate": gate,
                    "dat_rows": len(a),
                    "clean_sheet_rows": len(t),
                    "dat_matches_same_row_features_and_coefficient": bool(equal),
                    "tested_adjacent_pairs": len(c),
                    "q_rate_matches_change_per_excel_day": (
                        int(c[:, 0].sum()) if len(c) else 0
                    ),
                    "head_rate_matches_difference_per_day": (
                        int(c[:, 1].sum()) if len(c) else 0
                    ),
                    "head_rate_matches_sum_per_day": (
                        int(c[:, 2].sum()) if len(c) else 0
                    ),
                }
            )
    return findings


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument(
        "--output", type=Path, default=Path("results/legacy_input_audit.json")
    )
    a = p.parse_args()
    result = audit(a.source)
    a.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
