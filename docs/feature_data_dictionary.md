# Feature Data Dictionary — 2025 Flight Delay Prediction

## Purpose and prediction point

The supervised task is to predict whether an eligible US domestic flight will arrive **15 minutes or more late**. Prediction is assumed to occur **before scheduled departure**. The curated `v2` output contains **13 columns: 12 schedule/identity/derived columns and one outcome label**. Not every non-target column must be used as a model input. No model was trained in Phase 1.

Source: US Bureau of Transportation Statistics (BTS) Reporting Carrier On-Time Performance monthly 2025 CSV data. The processed table is produced by `notebooks/07_production_etl.ipynb` and stored as partitioned Parquet at `abfss://processed@stflight60106354.dfs.core.windows.net/flight_delays/2025/v2/clean_parquet/`. Curated output is at `abfss://curated@stflight60106354.dfs.core.windows.net/flight_delays/2025/v2/model_ready/`.

## Curated schema and availability

| Column | Output type | Source / derivation | Available at prediction time? | Role and leakage consideration |
|---|---|---|---|---|
| `FlightDate` | date | Parse BTS `FlightDate` | Yes, scheduled service date | Primarily temporal splitting/metadata; do not let future observations influence earlier training |
| `Year` | integer | Cast BTS `Year` | Yes | All selected data are 2025; constant and unlikely to help prediction |
| `Month` | integer | Cast BTS `Month` | Yes | Calendar seasonality; also Parquet partition field |
| `Reporting_Airline` | string | Trim BTS `Reporting_Airline` | Yes | Scheduled operating/reporting carrier; categorical encoding needed for a later model |
| `Origin` | string | Trim BTS `Origin` | Yes | Origin airport code; categorical predictor |
| `Dest` | string | Trim BTS `Dest` | Yes | Destination airport code; categorical predictor |
| `CRSDepTime` | integer | Cast BTS `CRSDepTime` (HHMM) | Yes | Scheduled departure clock time, **not** actual departure time; convert to usable time representation for modeling |
| `DepHour` | integer | `floor(CRSDepTime/100)`, with 2400 mapped to 0 | Yes | Scheduled hour from 0–23; correlated by construction with `CRSDepTime` |
| `DayOfWeek` | integer | Spark `dayofweek(FlightDate)` (Sunday=1, Saturday=7) | Yes | Day-of-week predictor |
| `IsWeekend` | integer (0/1) | 1 if `DayOfWeek` is 1 or 7, else 0 | Yes | Derived weekend indicator; redundant with day-of-week but interpretable |
| `Quarter` | integer | Spark `quarter(FlightDate)` (1–4) | Yes | Seasonal indicator derived from flight date; overlaps with month |
| `Route` | string | Join `Origin` and `Dest` with `-` | Yes | Route-specific patterns; high cardinality and overlaps with airports |
| `ArrDel15` | integer (0/1) | BTS label cast from `ArrDel15`; verified against BTS `ArrDelay >= 15` | **No** | **TARGET ONLY**; known only after flight outcome; must be separated from model input features |

Types are based on the conversion and selection logic in the production notebook, not an independently exported Unity Catalog schema dump.

## Raw source fields used for validation but excluded from curated predictors

- `DayofMonth` is checked against the parsed `FlightDate`.
- `Cancelled` and `Diverted` identify records excluded from the eligible-arrival population.
- `ArrDelay` verifies the label and is retained in the *processed* dataset for audit, but is **excluded from the curated model-ready dataset** because it would leak the answer.
- `Flight_Number_Reporting_Airline` is used with date, airline, origin, destination and scheduled departure time as a candidate duplicate key for raw-data inspection; it is not in the curated 13 columns.

## Data integrity, population and data risks

- Raw: 7,001,619 records; valid for the selected task: 6,879,484; excluded: 122,135; accepted share: 98.26%.
- Duplicate inspections found 0 exact duplicates and 0 extra records under the six-field candidate flight key in the raw input. This does not prove there are no near duplicates or mislabeled flights.
- The quality gate rejects publication if the acceptance rate is below 90% or the dataset is empty; the independent test notebook checks this gate on synthetic invalid input without writing to Azure.
- Only flights with known valid arrival outcomes are included. Delay estimates from this population should **not** be generalized to all scheduled flights, including cancellations and diversions.
- For Phase 2, separate the target `ArrDel15` from predictors; fit encoders/statistics on the training period only, use chronological train/validation/test splits and compare delayed-class F1 with a majority-class baseline. Treat `FlightDate` principally as split metadata and review redundant/constant columns before training.

## Version and lineage

```text
BTS 2025 source ZIPs + manifest (raw/v1)
  -> 12 extracted source CSVs (raw/flight_delays/2025/csv/)
  -> 07_production_etl: parse, validate, filter, derive features
  -> processed/flight_delays/2025/v2/clean_parquet/ (includes ArrDelay for audit)
  -> curated/flight_delays/2025/v2/model_ready/ (13 columns; excludes ArrDelay)
  -> Unity Catalog: flights_clean_2025_v2 and flights_features_2025_v2
  -> 06_pipeline_verification and 09_rejection_reason_analysis (read-only checks)
```

The original exploratory `v1` tables remain separate from the production `v2` outputs; matching aggregate counts do not prove exact row-by-row equality.
