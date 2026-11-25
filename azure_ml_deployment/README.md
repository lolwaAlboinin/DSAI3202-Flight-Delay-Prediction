# Flight Delay Prediction — Azure ML Online Deployment

Deployment assets for the **DSAI3202 Flight Delay Prediction Phase 2** project.

## Deployment settings

- Endpoint: `flight-delay-60106354` (key authentication)
- Deployment: `blue` on `Standard_DS3_v2`, one instance
- Model: `azureml:flight-delay-random-forest:1`
- Environment: `azureml:flight-delay-inference-env:2`
- Scoring entry point: `src/score.py`
- Classification decision threshold: `0.55`
- Nine input features: `Reporting_Airline`, `Origin`, `Dest`, `Month`, `CRSDepTime`, `DepHour`, `DayOfWeek`, `IsWeekend`, `Quarter`

## Files

- `endpoint.yml` — online endpoint definition
- `deployment.yml` — model, environment and managed compute configuration
- `src/score.py` — model loading, feature validation and probability-based prediction
- `valid_request.json` — example valid flight input
- `invalid_request.json` — invalid flight input (missing `Origin`)

## Verified tests (November 2026)

- Azure ML deployment provisioning: **Succeeded**; live traffic allocated to `blue`: **100%**
- Valid request: `prediction=1`, `delay_probability=0.606826418671098`, `threshold=0.55`
- Invalid request: returns `status=error`, `error_type=InvalidInput`, and an explanation that `Origin` is missing. This is application-level error reporting, **not** an HTTP 400 response.
- Offline vs. online consistency for the test flight: same probability and label, absolute difference `0.0`
- Five Cloud Shell CLI invocation times: 4558.60, 5562.74, 4215.36, 4815.99, 4191.25 ms; mean **4668.79 ms**. These measurements include CLI startup, authentication and network overhead; they are **not pure inference latency**.

## Example CLI commands

Requires access to the Azure subscription/workspace, Azure CLI and the Azure ML CLI extension. The registered model and environment must already exist.

```bash
RG=rg-dsai3202-lolwa-60106354
WS=mlwdsai320260106354

az ml online-endpoint create -f endpoint.yml -g "$RG" -w "$WS"
az ml online-deployment create -f deployment.yml -g "$RG" -w "$WS" --all-traffic
az ml online-endpoint invoke -n flight-delay-60106354 --deployment-name blue --request-file valid_request.json -g "$RG" -w "$WS"
az ml online-endpoint invoke -n flight-delay-60106354 --deployment-name blue --request-file invalid_request.json -g "$RG" -w "$WS"
```

**Do not execute the `create` commands against an endpoint that already exists.** Use `az ml online-deployment update -f deployment.yml` when editing an existing deployment. Running managed compute may incur charges.

## Repository safety

Do not commit Azure endpoint keys, credentials, private datasets, or serialized untrusted model files. This package contains configuration, scoring source and sample requests only. The model artifact and environment are referenced by Azure ML registry versions, not bundled here.
