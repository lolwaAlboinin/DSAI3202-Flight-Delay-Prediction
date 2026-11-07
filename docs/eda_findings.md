# Exploratory Data Analysis Findings — Full Accepted 2025 Flight Population

## Dataset and analysis scope

The analysis used the 2025 BTS records that passed the project validation rules. The real EDA notebook (`notebooks/03_eda.ipynb`) reads the registered `flights_features_2025` table (original `v1` curated data); the independent production `v2` and registered `v2` feature table had matching headline record counts and delay counts. **The charts are population-level summaries of 6,879,484 accepted flights, not estimates from the earlier synthetic sample.** The original dataset contained 7,001,619 raw records.

## Observed distribution

| Outcome | Records | Share of accepted flights |
|---|---:|---:|
| Not delayed (`ArrDel15=0`) | 5,344,846 | 77.69% |
| Delayed >=15 minutes (`ArrDel15=1`) | 1,534,638 | 22.31% |
| Total accepted | 6,879,484 | 100.00% |

The 22.31% delayed class is a minority. **Accuracy alone can hide poor delayed-flight detection**, so delayed-class precision, recall and F1 should be reported in the later modeling phase. A majority-class (always predict on-time) baseline would have about 77.69% accuracy on this population; that is a descriptive, in-sample class-prevalence baseline, not a held-out test result.

## Airline and scheduled-departure-hour patterns

- The ten busiest reporting airlines show different observed proportions of flights arriving at least 15 minutes late (see [`30_real_airline_delay_rates.png`](../evidence/30_real_airline_delay_rates.png)). Comparisons are descriptive; they do not establish airline-caused differences because routes, schedules, weather and selection into the accepted population may differ.
- The hourly chart ([`31_real_departure_hour.png`](../evidence/31_real_departure_hour.png)) shows lower observed delay rates for some early scheduled departures and higher rates later in the day. In the saved project results, an early hour near 05:00 was about 8.85%, while the evening peak around 19:00 was about 32.5%; these are rounded visual/analysis observations, not a causal conclusion.
- `Month`, `Quarter`, `DayOfWeek`, `DepHour`, airline and route are plausible schedule-available features for the project hypothesis. `Quarter` derives from month and `Route` derives from airports, so later feature selection may simplify overlapping representations.

## Data quality and rejected-record analysis

| Primary reason (one per rejected flight) | Flights | Share of rejected |
|---|---:|---:|
| Cancelled | 102,876 | 84.23% |
| Diverted | 19,258 | 15.77% |
| Missing arrival delay (remaining flight) | 1 | <0.01% |
| **Total rejected** | **122,135** | **100%** |

The overlapping-reasons view in `09_rejection_reason_analysis` also reports missing arrival delay/invalid labels on many cancelled or diverted flights. **Do not sum overlapping counts**: a single flight can have several flags. The primary-reason table uses a priority rule and counts each rejected record once. No raw duplicates were found by the exact-duplicate and candidate-key checks.

## Correlations, outliers and modeling risks

- The airline and hour charts show **associations**, not causal effects or Pearson correlation coefficients. A numerical correlation matrix and route-level outlier analysis were **not calculated** by the supplied real-data notebooks; neither should be claimed as completed.
- `ArrDelay` is measured in minutes and can include early (negative) arrivals and large positive delays. The Phase 1 binary label collapses these magnitudes into a >=15-minute threshold. The present EDA emphasizes the binary outcome and categorical/time group rates; the distribution of extreme arrival delays has not yet been quantified.
- **Selection bias:** Cancellation and diversion are removed because valid arrival-delay labels are unavailable. Results describe eligible completed flights, not the full population of scheduled flights. This limitation should accompany any reported delay percentage.
- **Target leakage:** Actual `ArrDelay` and other post-departure/outcome variables must not enter the predictors. `ArrDel15` is retained as the training target only.
- **Class imbalance:** About 22% delayed; use delayed-class F1 and confusion matrix, not accuracy alone.
- **Time leakage:** Use the documented later 2025 temporal holdout; fit transformations on training dates only. If the raw flight date is included as metadata, it should not directly leak test-period outcomes into training.
- **Operational risk:** The production Parquet publisher uses `overwrite`. The quality gate checks acceptance before publishing, but two output writes are not an atomic transaction; reruns should be controlled and backed up as needed.

## Evidence and scope limits

- [`29_real_delay_distribution.png`](../evidence/29_real_delay_distribution.png)
- [`30_real_airline_delay_rates.png`](../evidence/30_real_airline_delay_rates.png)
- [`31_real_departure_hour.png`](../evidence/31_real_departure_hour.png)
- [`49_real_quality_recheck.png`](../evidence/49_real_quality_recheck.png)
- [`50_rejection_reason_counts.png`](../evidence/50_rejection_reason_counts.png)
- [`51_primary_rejection_reasons.png`](../evidence/51_primary_rejection_reasons.png)

**Conclusion for Phase 1:** The accepted population is large enough for future temporal modeling and contains usable schedule-time features. Careful evaluation is still necessary because of label imbalance, removal of cancelled/diverted flights, temporal drift and the possibility of noncausal group differences. No trained model performance is reported in Phase 1.
