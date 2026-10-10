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

`example_history.csv`: a 12-observation Doulong sequence selected from the 2006 holdout, ending before a scored forecast. It is an inference-input example, not additional training data.

`provenance.json`: original relative paths and SHA-256 hashes. Data were exported with `scripts/import_sources.py`; that script requires `xlrd` and the two original author-held workbooks. Normal users can reproduce both experiments from the CSV without those workbooks.

See `results/data_quality.json` and `results/excluded_observations.csv` for cleaning decisions and `docs/RIGHTS.md` for reuse status.
