"""Read the two original workbooks without changing them; export traceable records."""

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import xlrd

GATES = {
    "射阳河闸": "sheyang",
    "黄沙港闸": "huangsha",
    "斗龙港闸": "doulong",
    "新洋港闸": "xinyang",
}
SHORT = {"sheyang": "射阳", "huangsha": "黄沙", "doulong": "斗龙", "xinyang": "新洋"}


def extract(source, output):
    output.mkdir(parents=True, exist_ok=True)
    rows, manifest = [], []
    for year in (2003, 2006):
        rel = Path("2-专利撰写/处理过程/03 06") / f"{year}闸门流量资料--整理.xls"
        path = source / rel
        book = xlrd.open_workbook(path)
        manifest.append(
            {
                "path": rel.as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
        for sheet in book.sheets():
            headers = sheet.row_values(0)
            for i in range(1, sheet.nrows):
                values = dict(zip(headers, sheet.row_values(i)))
                stamp = values["时间"]
                if not isinstance(stamp, (int, float)) or stamp <= 0:
                    continue  # wholly blank non-observation rows

                def number(v):
                    return float(v) if isinstance(v, (int, float)) else np.nan

                rows.append(
                    {
                        "gate": GATES[sheet.name],
                        "timestamp": xlrd.xldate_as_datetime(stamp, book.datemode)
                        .replace(microsecond=0)
                        .isoformat(),
                        "upstream_m": number(values["闸上水位"]),
                        "downstream_m": number(values["闸下水位"]),
                        "discharge_m3s": number(values["流量"]),
                        "remark": str(values.get("备注", "")),
                        "source_year": year,
                        "source_sheet": sheet.name,
                        "source_row": i + 1,
                    }
                )
    df = pd.DataFrame(rows)
    df.to_csv(output / "observations.csv", index=False, float_format="%.10g")
    geometry = []
    for gate, short in SHORT.items():
        p = (
            source
            / "5-转英文-Water/修改意见/2006"
            / f"2006-{short}"
            / f"2006-{short}.xls"
        )
        sheet = xlrd.open_workbook(p).sheet_by_index(1)
        width = float(sheet.cell_value(1, 6))
        label = next(i for i in range(1, 8) if "Z0" in str(sheet.cell_value(i, 6)))
        sill = float(sheet.cell_value(label + 1, 6))
        geometry.append(
            {
                "gate": gate,
                "width_m": width,
                "sill_m": sill,
                "source_note": "Fixed study geometry from coefficient-calculation sheet; operating gate widths can vary.",
            }
        )
        manifest.append(
            {
                "path": p.relative_to(source).as_posix(),
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
        )
    pd.DataFrame(geometry).to_csv(output / "geometry.csv", index=False)
    (output / "provenance.json").write_text(
        json.dumps(
            {
                "records": len(df),
                "sources": manifest,
                "origin": "Author-supplied research archive; 2003 and 2006 observations",
                "publication": "https://doi.org/10.3390/w17091248",
                "original_software": "Proprietary training module; not included",
                "import": "scripts/import_sources.py",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(df.groupby(["source_year", "gate"]).size().to_string())


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument("--output", type=Path, default=Path("data"))
    a = p.parse_args()
    extract(a.source, a.output)
