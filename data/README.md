# Data dictionary

`observations.csv`: one time-stamped observation or operation-marker row, before model cleaning. 1,309 records. No synthetic data.

| Column | Meaning |
|---|---|
| gate | doulong, huangsha, sheyang, xinyang |
| timestamp | Original local measurement time; timezone unspecified |
| upstream_m / downstream_m | Recorded upstream/downstream water level, metres; original datum |
| discharge_m3s | Measured discharge, cubic metres per second |
| remark | Original operating remark; numeric zero generally marks an empty note, not a gate state |
| source_year / source_sheet / source_row | Original workbook year, sheet, one-based Excel row |

`geometry.csv`: study gate width and sill elevation in metres, using the same datum as the original water levels. Fixed values do not encode changing gate openings.

`provenance.json`: original workbook-relative paths and SHA-256 hashes. `scripts/import_sources.py` documents the CSV export from the two source workbooks.

The included records cover four gates in 2003 and 2006. They retain observed values, source-row identifiers and operation-marker rows. Check timestamp order, missing values, operation remarks, time units and the applicability of the submerged-flow equation before constructing a training dataset. The observation export does not define a train/test split.

See [research method](../docs/METHOD.md), [published results](../docs/PUBLISHED_RESULTS.md) and [material-use information](../docs/RIGHTS.md).
