# Execution evidence

This folder contains **selected screenshots from the actual Azure/Databricks project workflow**. Verify personally identifiable information and obscure it before changing the repository visibility or granting broad access. They demonstrate outputs, not a substitute for code or independent reruns.

## Key evidence

- `05_all_zip_hashes_verified.png` — source manifest verification.
- `06_safe_ingestion_rerun.png` — files already present were skipped on rerun.
- `19_real_quality_results.png` — 2025 raw, accepted and rejected rows.
- `37_duplicate_inspection.png`, `38_flight_key_duplicates.png` — duplicate checks.
- `29_real_delay_distribution.png`, `30_real_airline_delay_rates.png`, `31_real_departure_hour.png` — real EDA.
- `32_unity_catalog_lineage.png`, `33_lineage_graph.png` — lineage view.
- `43_production_job_output.png` — independent production job succeeded.
- `44_production_v2_catalog.png`, `45_production_v2_verification.png` — v2 catalog verification.
- `46_invalid_test_input.png`, `47_invalid_input_validation.png`, `48_quality_gate_blocks_publication.png` — synthetic independent bad-input gate check. Not an end-to-end failed production job.
- `49_real_quality_recheck.png`, `50_rejection_reason_counts.png`, `51_primary_rejection_reasons.png` — full real-data rejection breakdown.

Screenshots are grouped here without storing BTS raw data or credentials.
