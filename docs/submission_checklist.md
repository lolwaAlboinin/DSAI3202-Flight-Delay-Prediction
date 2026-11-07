# Phase 1 Submission Checklist — based on official DSAI3202 Project Phase 1 v2 rubric

## Confirmed implemented from code and screenshots
- [x] Unique public BTS flight dataset, 2025 monthly files, >1 GB uncompressed
- [x] 12 monthly CSV files, batch ingestion, original ZIPs in versioned Azure raw path
- [x] Real row accounting and 90% quality threshold
- [x] Duplicate inspection and target-leakage controls
- [x] Processed and curated Parquet output, including versioned v2 production output
- [x] Databricks production job completed successfully (November 7, 2026)
- [x] EDA summary and charts based on full accepted population
- [x] v1/v2 Unity Catalog tables, verification and available lineage view
- [x] 13-column model-ready dataset (12 input/metadata fields + target)

## Still requires action/evidence before declaring submission complete
- [x] Add `scripts/safe_ingestion.ps1` and `data_manifest/manifest.csv` to this package
- [x] Include `06_safe_ingestion_rerun.png` (12 ZIPs plus manifest skipped); hash validation screenshots also included. Confirm remote identity independently if the rubric requires stronger proof than size checks.
- [x] Separate-input row-level validation and gate test (`08_quality_failure_test.ipynb`, `46`–`48` screenshots) rejects 6 of 10 input records and triggers failure at 40%; no writes performed. This is NOT a failed production-job run.
- [x] Real rejected-record reason breakdown (`09_rejection_reason_analysis.ipynb`, `49`–`51` screenshots), including overlapping and single-primary reasons; add additional outlier/correlation discussion if required
- [ ] Provide feature data dictionary: definitions, types, source fields, prediction-time availability and leakage risk
- [ ] Confirm actual source schema, keys, assumptions, raw→processed→curated lineage diagram
- [ ] Review/redact included evidence screenshots for user/account information before changing repository visibility or sharing access
- [ ] Record a measured or estimated cost/performance optimization and compute cleanup procedure
- [ ] Supply exact runtime version and exported portal job config if available
- [x] README includes AI-use disclosure for proposal, code, notebook review and documentation; confirm exact wording meets instructor form
- [ ] Ensure topic/hypothesis revisions and use of Databricks Jobs instead of originally proposed Azure Data Factory are documented (and approved if required)
- [ ] Create repo, meaningful commits, give instructor access, submit repository URL plus final commit SHA on D2L

## Not required in Phase 1 unless separately instructed
- A trained Random Forest model, model accuracy or F1 results (hypothesis provides a baseline and Phase 2 plan)
- Azure ML model endpoint
- Managed feature store or Microsoft Purview

**Do not claim full marks or final completion until the remaining rubric evidence has been verified.**
