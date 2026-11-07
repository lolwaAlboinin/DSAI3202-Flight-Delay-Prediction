# Databricks Job Setup (documented UI configuration)

**Production job:** `Flight_Delay_Phase1_Production`  
**Job ID:** `284953812719686`  
**Task:** `run_production_etl`  
**Notebook:** `notebooks/07_production_etl` (workspace path under `Flight_Delay_Phase1`)  
**Compute:** `flight-delay-phase1-60106354` (existing approved cluster)  
**Execution:** manual `Run now`; no recurring trigger  
**Verified run ID:** `88050464054187`  
**Run date:** November 7, 2026  
**Status:** Succeeded  
**Duration:** 1m 42s

**Verification job:** `Flight_Delay_Phase1_Verification`  
**Job ID:** `818019740584801`  
**Task:** `verify_flight_pipeline`  
**Verified earlier run ID:** `1096722264794361` (v1 check)

## Recreate manually

1. Import the notebooks into a `Flight_Delay_Phase1` folder in the Azure Databricks workspace.
2. Start the approved cluster with Unity Catalog and ADLS access.
3. Create a Databricks Job, choose Notebook task `07_production_etl` and select the cluster.
4. Run manually, inspect the output and record the new run ID.
5. After successful publication, register/verify v2 external tables using `05_catalog_and_lineage`.
6. Run `06_pipeline_verification` (v1 and v2 checks).

This documents a portal-built job; it is NOT an exported Databricks Jobs API JSON definition. Export the actual job configuration from Databricks if the course requires a machine-readable configuration file.
