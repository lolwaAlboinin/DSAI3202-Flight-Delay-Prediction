# Flight Delay Prediction — DSAI3202 Phase 1

Cloud data foundation for predicting whether a US domestic flight arrives at least **15 minutes late**, using 2025 US Bureau of Transportation Statistics (BTS) on-time reporting data. This repository contains the reproducible PySpark notebook logic and setup notes; the large data remains in Azure Data Lake Storage Gen2.

> **Status (November 7, 2026):** An independent production Databricks ETL job succeeded. Nine notebooks, ingestion script, source manifest and selected execution screenshots are packaged; see [`docs/submission_checklist.md`](docs/submission_checklist.md) for evidence and rubric items not yet completed. Do not treat the checked pipeline as evidence of model training.

## Project and hypothesis

**Problem:** Flight arrival delays affect passenger planning and airline operations.  
**Task:** Binary classification of `ArrDel15`: **1** if actual arrival delay is at least 15 minutes, **0** otherwise, on flights with known valid arrival outcomes.  
**Hypothesis (from project proposal):** A Random Forest classifier using airline, origin, destination, scheduled departure time, month and day of week will have better **delayed-class F1-score** than a majority-class baseline on later 2025 flights.  
**Baseline/experiment plan:** Train January–August, validate September–October, and test November–December 2025; compare delayed-class F1, accuracy and confusion matrix to a majority-class baseline. **No model training is reported in Phase 1.**  
**Implementation refinement:** The original hypothesis proposed Azure Data Factory; the implemented Phase 1 automation uses an Azure Databricks Job. Confirm/record this refinement with the instructor if approval is required.

## Dataset and architecture

**Dataset:** [BTS Reporting Carrier On-Time Performance](https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ), 12 monthly ZIP/CSV files for January–December 2025. The earlier verified download was approximately **2.95 GiB uncompressed** (well above the required ~1 GB) and yielded **7,001,619** flight records. Source ZIPs and receipt/manifest were stored in Azure; do not commit the raw data or sensitive access information to GitHub.

**Ingestion mode:** Repeatable batch download/upload of the 12 fixed 2025 files. **Refresh strategy:** Preserve the fixed 2025 input as a versioned historical snapshot; for future years, use new version/year paths and a new manifest rather than overwriting the preserved 2025 source. The ingestion script is included at [`scripts/safe_ingestion.ps1`](scripts/safe_ingestion.ps1) and its source receipt at [`data_manifest/manifest.csv`](data_manifest/manifest.csv). The script requires an authenticated Azure CLI session with appropriate storage permissions and the local BTS ZIP files; no account keys are stored here.

**Azure architecture:**

```text
BTS public monthly ZIP/CSV files (2025)
  │  batch download + manifest/hash check
  ▼
Azure Data Lake Storage Gen2 — raw/original ZIPs (v1) + 12 CSVs
  │  Databricks Spark reads raw/flight_delays/2025/csv/
  ▼
Azure Databricks — validate types, dates, labels, cancellations,
                   diversions, duplicates and ≥90% acceptance gate
  │
  ▼
ADLS Gen2 processed/flight_delays/2025/v2/clean_parquet/
  │  feature construction and drop outcome leakage fields
  ▼
ADLS Gen2 curated/flight_delays/2025/v2/model_ready/
  │
  ├── Unity Catalog: flights_clean_2025_v2 / flights_features_2025_v2
  └── Verification notebook / EDA / evidence

Azure Databricks Job: Flight_Delay_Phase1_Production
```

**Versions:** Original preserved ZIPs are at `raw/flight_delays/2025/v1/`; extracted CSV input at `raw/flight_delays/2025/csv/`; exploratory processed/curated tables use `v1`; the independent verified production job writes to processed/curated `v2`. All `v1` and `v2` checks matched on key aggregate results. **Equal aggregates do not prove row-by-row equivalence.**

**Source schema and assumptions:** BTS source has ~110 columns; project checks year, month, flight date, airline, airports, scheduled departure time, cancellation/diversion, `ArrDelay`, and `ArrDel15`. Candidate duplicate key: `(FlightDate, Reporting_Airline, Flight_Number_Reporting_Airline, Origin, Dest, CRSDepTime)`; duplicate checks on the 2025 raw input returned zero extra rows. Scheduled departure time 2400 is normalized to hour 0. `ArrDel15` is the supervised label, not a predictor. Cancelled/diverted flights and invalid/unknown outcomes are rejected, so results refer only to the accepted-flight population.

See [`config/environment.md`](config/environment.md) for permissions and exact Azure objects. The complete [feature data dictionary](docs/feature_data_dictionary.md) documents definitions, output types, source fields, prediction-time availability, leakage risks and raw-to-curated lineage.

## Run the pipeline

**Prerequisites:** Azure Databricks Python/Spark cluster with Unity Catalog access to the storage account, read permission on raw CSVs, write permission on processed/curated containers, and 12 intact monthly CSV files. Spark/PySpark and `dbutils` come from the runtime; matplotlib/pandas are used for EDA. See [`requirements.txt`](requirements.txt).

1. Obtain authorized Azure Databricks/ADLS access from the course workspace administrators. Do not commit tokens, secrets or credentials.
2. Import `notebooks/` into the Databricks workspace (or import the original workspace source files as appropriate).
3. Confirm source directory has exactly 12 monthly CSVs: `abfss://raw@stflight60106354.dfs.core.windows.net/flight_delays/2025/csv/`.
4. Run `07_production_etl` on the permitted project compute, or recreate and manually run the Databricks job in [`config/job_setup.md`](config/job_setup.md). **Warning:** this job uses `overwrite` on its v2 output paths. Confirm rerun safety/backup before executing again.
5. Use `05_catalog_and_lineage` to register/verify v2 external Parquet tables, then run `06_pipeline_verification` (v1 and v2). Run `03_eda` for population-level charts (currently reads registered v1 feature table).
6. `01_ingest_and_validate` and `04_features` include historical v1 writes that use `overwrite`; they are documentation/exploration, not prerequisites for the independent production job. `02_clean_and_transform` checks stored v1 results. `08_quality_failure_test` and `09_rejection_reason_analysis` are independent read-only checks; do not depend on them for production publishing.

**Job evidence:** [`config/job_setup.md`](config/job_setup.md) records names, manual configuration, successful run ID, and 1m42s elapsed time. Selected evidence screenshots are under [`evidence/`](evidence/README.md); review and redact personal information before publishing the repository or sharing wider access.

## Results and features

| Measure | Actual 2025 run |
| --- | ---: |
| Source rows | 7,001,619 |
| Quality accepted | 6,879,484 |
| Quality rejected | 122,135 |
| Acceptance rate | 98.26% |
| Processed v2 rows | 6,879,484 |
| Curated v2 rows | 6,879,484 |
| Delayed accepted flights (`ArrDel15=1`) | 1,534,638 |
| On-time accepted flights (`ArrDel15=0`) | 5,344,846 |
| Delay rate among accepted flights | 22.31% |

**Quality policy:** Parse and validate year/month/day/date, airline and airport fields, scheduled departure time, cancellation/diversion, actual arrival outcome and label consistency. Rejection reasons include cancelled/diverted or otherwise non-modelable records; **primary rejection reasons were measured on the full input: 102,876 cancelled flights, 19,258 diverted flights and 1 record with missing arrival delay.** The production job blocks publication when the overall acceptance rate is below 90% or the dataset is empty. Notebook `08_quality_failure_test` additionally validates 10 separate synthetic rows (4 accepted, 6 rejected), then confirms the 40% acceptance rate triggers the 90% gate. This is a **read-only separate-input controlled test**, not a failed production-job run or an atomic-publication guarantee. Notebook `09_rejection_reason_analysis` reconstructs the production validation over the real BTS input and reports primary and overlapping rejection reasons. See checklist.

**Rejection analysis:** Primary categories sum to 122,135 rejected flights: cancelled 102,876 (84.23%), diverted 19,258 (15.77%) and missing arrival delay 1 (<0.01%). The overlapping-reasons view may count a record more than once; the primary categories assign one reason per rejected record. These outcomes are intentionally excluded from the valid-arrival population, which can create selection bias.

**EDA:** Overall delayed share 22.31%. Airline delay proportions differ across the busiest carriers; scheduled departure hour also shows meaningful differences. These are **observed associations, not causal findings or calculated correlation coefficients**; cancelled/diverted flights are excluded and may introduce selection bias. See [full EDA findings and limitations](docs/eda_findings.md) for distribution, chart interpretations, outlier scope and implications for modeling.

**Model-ready columns (13 total):** `FlightDate` (date, scheduling date); `Year` (int, year); `Month` (int, month); `Reporting_Airline` (string, known airline); `Origin` (string, origin airport); `Dest` (string, destination airport); `CRSDepTime` (int, scheduled departure HHMM); `DepHour` (int, derived scheduled hour); `DayOfWeek` (int, day number); `IsWeekend` (int, derived weekend flag); `Quarter` (int, derived quarter); `Route` (string, origin-destination pair); `ArrDel15` (int, target **known only after flight arrival**).

See the [feature data dictionary](docs/feature_data_dictionary.md) for a per-column schema, sources and prediction-time availability. All twelve non-target fields are derived from scheduled or identifying flight attributes and are intended to be available before departure. `ArrDelay` and actual departure/arrival outcome fields are excluded to prevent leakage. The flight date may be used to create temporal train/validation/test splits rather than as a raw model predictor. The feature set has not been encoded or trained yet.

## Reproducibility and evidence

The project includes **nine** Databricks notebooks in `notebooks/`, ingestion source in `scripts/`, an actual source manifest in `data_manifest/`, and selected successful-execution screenshots in `evidence/`. Notebook outputs are intentionally removed from source copies; the original workspace contains successful run outputs and screenshots give an auditable subset of the results. The external tables initially used v1; production outputs and matching v2 catalog tables were later registered. For data quality, inspect notebooks `08` and `09` as well as `07`. No 2025 raw CSV/ZIP datasets or Azure secrets are committed.

## Resource use and contributions

**Resource/performance evidence:** The manually launched Databricks production job completed in **1 minute 42 seconds** on the existing course project cluster, reading 12 CSVs and verifying ~6.88 million curated rows. Reusing an approved shared/existing cluster avoided provisioning another separate compute resource for this course project; actual billed cost has not been measured. Re-running overwrites v2 and incurs additional compute; the job has no recurring schedule.

**Cleanup:** Stop/terminate project compute when not needed (subject to course cluster policy), remove unused temporary runs/test resources after evidence capture, and review ADLS storage firewall/access settings with the instructor. Do **not** delete preserved raw `v1` data, submitted v2 results or catalog tables without authorization.

**Contributions:** Individual project. Student performed dataset selection/download, validation, Azure upload, Databricks execution, output verification and evidence capture. ChatGPT assisted with planning, explanations, code drafting and README organization; manual results and approval remain the student's responsibility. Original BTS flight data and methodology belong to their respective publishers; adapt code from course labs only with appropriate attribution if reused.

## AI use

| Tool | Request | Response | My changes / verification |
| --- | --- | --- | --- |
| ChatGPT | Help choose a cloud project and write the flight-delay hypothesis | Proposed BTS flight data, prediction question, evaluation plan | Selected 2025 data, validated source size and revised experiment to use temporal splits and delayed-class F1 |
| ChatGPT | Help create ingestion, quality, feature engineering and production Databricks code | Drafted PySpark notebook logic and step-by-step Azure instructions | Executed notebooks/jobs on real data, checked actual row counts and errors, handled permissions and saved evidence |
| ChatGPT | Check notebooks and prepare project documentation | Suggested cleanup, v1/v2 catalog clarification, README structure | Removed sample-only EDA/feature cells, verified real 2025 outputs, added separate-input quality and real rejection-reason notebooks, and reviewed final README and evidence |

