# Flight Delay Prediction — DSAI3202 (Phases 1 and 2)

End-to-end cloud computing project predicting whether a US domestic flight arrives at least **15 minutes late**, using 2025 US Bureau of Transportation Statistics (BTS) on-time reporting data. **Phase 1** covers Azure data ingestion, quality checks, feature engineering and a repeatable Databricks production pipeline. **Phase 2** adds chronological data splitting, Random Forest training, final holdout evaluation and a working Azure Machine Learning managed online endpoint. The large dataset remains in Azure Data Lake Storage Gen2.

> **Status (November 25, 2026):** Phase 1 ETL was successfully verified. Phase 2 trained and evaluated a Random Forest model, registered it in Azure ML and verified the online deployment (`blue`, 100% traffic), valid/invalid requests and an exact offline–online prediction match for one example. The repository contains 14 notebooks, deployment configuration and selected evidence. See [`docs/submission_checklist.md`](docs/submission_checklist.md) for the original Phase 1 checklist; check the current Phase 2 submission rubric separately.

## Project and hypothesis

**Problem:** Flight arrival delays affect passenger planning and airline operations.  
**Task:** Binary classification of `ArrDel15`: **1** if actual arrival delay is at least 15 minutes, **0** otherwise, on flights with known valid arrival outcomes.  
**Hypothesis (from project proposal):** A Random Forest classifier using airline, origin, destination, scheduled departure time, month and day of week will have better **delayed-class F1-score** than a majority-class baseline on later 2025 flights.  
**Baseline/experiment:** The planned chronological split was implemented in Phase 2: train January–August, validate September–October and test November–December 2025. Majority-class baseline and Random Forest predictions were evaluated on later flights. The delayed-class F1 objective is assessed on held-out data below.  
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

See the [feature data dictionary](docs/feature_data_dictionary.md) for a per-column schema, sources and prediction-time availability. All twelve non-target fields are derived from scheduled or identifying flight attributes and are intended to be available before departure. `ArrDelay` and actual departure/arrival outcome fields are excluded to prevent leakage. The flight date may be used to create temporal train/validation/test splits rather than as a raw model predictor. For Phase 2, nine predeparture predictors were selected, and the training notebook fitted the model and preprocessing pipeline.

## Phase 2 — model training and evaluation

Phase 2 uses the curated 2025 flight data from Phase 1 and preserves a versioned, chronological training snapshot in ADLS Gen2. Splitting by flight date avoids evaluating on earlier records than those used for training.

| Split | Period | Accepted flight records |
| --- | --- | ---: |
| Training | January–August 2025 | 4,592,366 |
| Validation | September–October 2025 | 1,159,898 |
| Test | November–December 2025 | 1,127,220 |

**Training:** A scikit-learn Random Forest and its preprocessing pipeline were fitted using a deterministic training sample of **91,931** records, with a deterministic validation sample of **57,588** records. Training on samples was a practical compute choice; it is not the same as fitting on all 4.59 million training records. The decision threshold **0.55** was selected using validation data and kept unchanged for the held-out test and deployed endpoint.

**Nine inference features:** `Reporting_Airline`, `Origin`, `Dest`, `Month`, `CRSDepTime`, `DepHour`, `DayOfWeek`, `IsWeekend`, `Quarter`. The label `ArrDel15` and post-flight outcome information are excluded from the predictors.

**Final holdout evaluation:** A deterministic 5% sample of November–December flights (approximately 56,081 observations) was used for the reported final comparison.

| Metric | Majority-class baseline | Random Forest (threshold 0.55) |
| --- | ---: | ---: |
| Accuracy | 0.7624 | 0.6042 |
| Balanced accuracy | 0.5000 | 0.5842 |
| Delayed-class precision | Not reported here | 0.3106 |
| Delayed-class recall | Not reported here | 0.5460 |
| Delayed-class F1 | 0 for a zero-positive-prediction baseline | 0.3960 |
| ROC-AUC | Not reported here | 0.6150 |

The Random Forest improves recognition of delayed flights and balanced accuracy relative to predicting every flight as on time, **but its overall accuracy is lower** and it produces many false alarms. The recorded final error analysis reports **16,835 false positives** and **6,138 false negatives** on the held-out sample. The results should not be described as uniformly superior to the baseline. The evaluation covers accepted flights only; excluded cancellations/diversions and year-to-year changes limit generalization.

**Notebooks:** [`10_prepare_training_data`](notebooks/10_prepare_training_data.ipynb), [`11_baseline_model`](notebooks/11_baseline_model.ipynb), [`12_train_random_forest`](notebooks/12_train_random_forest.ipynb), [`13_final_model_evaluation`](notebooks/13_final_model_evaluation.ipynb), and [`14_prepare_model_deployment`](notebooks/14_prepare_model_deployment.ipynb).

## Phase 2 — Azure Machine Learning deployment

**Model traceability:** The deployed model is `azureml:flight-delay-random-forest:1`, using inference environment `azureml:flight-delay-inference-env:2`. The model was trained in [`12_train_random_forest`](notebooks/12_train_random_forest.ipynb) using a fitted preprocessing pipeline and deterministic training sample, then evaluated in [`13_final_model_evaluation`](notebooks/13_final_model_evaluation.ipynb). The source is the Phase 1 curated 2025 feature dataset, with the Phase 2 versioned snapshot `phase2_20251118_v1` in ADLS Gen2. The chronological split and snapshot creation are documented in [`10_prepare_training_data`](notebooks/10_prepare_training_data.ipynb). **Verified MLflow training run:** `3b5c8e7ea8ce490da766182e8db9f04b` (run name `Flight_Delay_RF_Phase2`; checked in saved outputs of `12_train_random_forest`). **MLflow model URI:** `models:/m-ef8f1d44e4d0475b9dfead71d2f4b78d`. The notebook also logs dataset version `phase2_20251118_v1`, random seed `42`, and the selected decision threshold `0.55`. The fitted preprocessing is preserved with the logged model; the notebook verified that predictions match after reloading it. **GitHub training-code commit:** not yet confirmed from repository history; use the commit containing the training notebook version used for the MLflow run, rather than assuming the latest README commit was used. The registered model version and the source code in this repository should be kept unchanged for assessment.


The trained Random Forest was registered in Azure ML as **`flight-delay-random-forest:1`**. A managed online endpoint named **`flight-delay-60106354`** uses the `blue` deployment, environment **`flight-delay-inference-env:2`** and one `Standard_DS3_v2` compute instance. At verification, the endpoint and deployment reported **Succeeded** and **100% of live traffic** was allocated to `blue`.

The deployment accepts JSON in the form `{"data": [{...nine features...}]}`. Its `score.py` validates the nine fields, loads the registered model and returns a predicted class, delay probability, threshold and model version.

**Verified online example:** `AA` from `RDU` to `PHL`, month 8, scheduled departure `1610`, `DepHour=16`, `DayOfWeek=7`, `IsWeekend=1`, `Quarter=3` returned **class 1 (delayed)** and probability **`0.606826418671098`** with threshold **0.55**. The same example evaluated from the saved model in Databricks returned the same probability and class, with an observed difference of **0.0**. This verifies **one input case**, not every possible flight.

**Input validation:** An intentionally invalid request missing `Origin` returns a structured application-level `InvalidInput` message identifying the missing field. This implementation returns the error object in a normal response; it does **not** claim HTTP 400 status handling.

**Observed latency:** Five sequential requests invoked through Azure Cloud Shell yielded **4558.60, 5562.74, 4215.36, 4815.99 and 4191.25 ms**; average **4668.79 ms** (approximately **4.67 s**). These are **client-observed Azure CLI invocation times**, including command startup, authentication/network and service processing, **not pure model inference latency**.

**Performance reference target:** A **6-second client-observed request time** is used here as a retrospective reference target, added after the five-request test (not a target claimed to have been selected in advance). The five measured requests ranged from **4.19 to 5.56 seconds**, so all five were below this reference value. A larger, repeated test under controlled load is needed to establish reliable p95 latency and throughput. This reference is for the **Cloud Shell CLI round trip**, not for model-only scoring.

Deployment source and usage instructions: [`azure_ml_deployment/`](azure_ml_deployment/). The environment and registered model are Azure ML assets referenced by version; the trained model file is **not committed** to this repository. Endpoint access requires authorized Azure access and may incur ongoing compute charges.

## Final presentation

**PowerPoint presentation:** [DSAI3202 Flight Delay Final Presentation](presentation/DSAI3202_Flight_Delay_Final_Presentation.pptx). This file explains the architecture, modeling choices, baseline comparison, error analysis, deployment, performance and live demonstration. **Note:** This link expects the presentation to be committed under `presentation/` with the exact filename shown; if the uploaded filename or folder is different, update this relative link accordingly.

**Live assessment:** The Azure ML managed endpoint must be accessible during the assigned D2L assessment and presentation slot on **December 1 or 3, 2026**. The instructor may supply a new valid JSON request that follows the nine-feature input contract. The endpoint may be removed between assessment windows to control cost and redeployed from the saved YAML, registered model, and inference environment; model/data assets must remain available. Verify operational readiness and authorized access before the live demonstration.

## Project repository structure and evidence

```text
notebooks/                  01–09 Phase 1; 10–14 Phase 2
azure_ml_deployment/        endpoint/deployment YAML, sample requests, src/score.py
config/                     Phase 1 environment and job setup
scripts/                    Ingestion script
data_manifest/              Source receipt/manifest
docs/                       Phase 1 documentation and checklist
evidence/                   Phase 1 screenshots
evidence/phase2/            Phase 2 training, evaluation and consistency screenshots
presentation/               Final project PowerPoint presentation
```

**Key Phase 2 evidence:** [`54_phase2_data_loading.png`](evidence/phase2/54_phase2_data_loading.png), [`55_phase2_data_split.png`](evidence/phase2/55_phase2_data_split.png), [`58_baseline_validation.png`](evidence/phase2/58_baseline_validation.png), [`60_random_forest_validation.png`](evidence/phase2/60_random_forest_validation.png), [`64_final_holdout_comparison.png`](evidence/phase2/64_final_holdout_comparison.png), [`65_final_holdout_error_analysis.png`](evidence/phase2/65_final_holdout_error_analysis.png), and [`70_offline_online_consistency.png`](evidence/phase2/70_offline_online_consistency.png). A dedicated endpoint-latency screenshot was not confirmed in the latest repository screenshot, though measured CLI output was recorded during testing.

**Reproducing Phase 2:** Access to the actual Databricks workspace, feature tables, ADLS snapshot, MLflow model artifact and Azure ML workspace is required. The notebooks and configurations document the workflow but the repository alone, without these cloud assets, is not a standalone one-click deployment. Do not run overwrite/redeployment commands on existing resources without checking their impact and cost.

## Reproducibility and evidence

The project includes **14** Databricks notebooks (nine Phase 1 and five Phase 2) in `notebooks/`, ingestion source in `scripts/`, an actual source manifest in `data_manifest/`, and selected successful-execution screenshots in `evidence/`. The original Databricks workspace contains run outputs; repository screenshots give an auditable subset of the actual results. The external tables initially used v1; production outputs and matching v2 catalog tables were later registered. Phase 2 model and deployment evidence is linked above. For data quality, inspect notebooks `08` and `09` as well as `07`. No 2025 raw CSV/ZIP datasets or Azure secrets are committed.

## Resource use and contributions

**Resource/performance evidence:** The manually launched Databricks production job completed in **1 minute 42 seconds** on the existing course project cluster, reading 12 CSVs and verifying ~6.88 million curated rows. Reusing an approved shared/existing cluster avoided provisioning another separate compute resource for this course project; actual billed cost has not been measured. Re-running overwrites v2 and incurs additional compute; the job has no recurring schedule.

**Cleanup:** Stop/terminate project compute when not needed (subject to course cluster policy), remove unused temporary runs/test resources after evidence capture, and review ADLS storage firewall/access settings with the instructor. Do **not** delete preserved raw `v1` data, submitted v2 results or catalog tables without authorization.

**Contributions:** Individual project. Student performed dataset selection/download, validation, Azure upload, Databricks execution, model training/evaluation, Azure ML endpoint testing, output verification and evidence capture. ChatGPT assisted with planning, explanations, code drafting and README organization; manual results and approval remain the student's responsibility. Original BTS flight data and methodology belong to their respective publishers; adapt code from course labs only with appropriate attribution if reused.

## AI use

| Tool | Request | Response | My changes / verification |
| --- | --- | --- | --- |
| ChatGPT | Help choose a cloud project and write the flight-delay hypothesis | Proposed BTS flight data, prediction question, evaluation plan | Selected 2025 data, validated source size and revised experiment to use temporal splits and delayed-class F1 |
| ChatGPT | Help create ingestion, quality, feature engineering and production Databricks code | Drafted PySpark notebook logic and step-by-step Azure instructions | Executed notebooks/jobs on real data, checked actual row counts and errors, handled permissions and saved evidence |
| ChatGPT | Check notebooks and prepare project documentation | Suggested cleanup, v1/v2 catalog clarification, README structure | Removed sample-only EDA/feature cells, verified real 2025 outputs, added separate-input quality and real rejection-reason notebooks, and reviewed final README and evidence |
| ChatGPT | Assist with Phase 2 modeling, deployment troubleshooting and documentation | Suggested notebook code, Azure ML YAML/scoring script, dependency fixes and test commands | Ran tests in Databricks and Azure, checked actual scores/statuses, corrected environment and invalid-input handling, and verified offline–online consistency |

