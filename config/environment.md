# Environment and Permissions

- Azure subscription with ADLS Gen2 storage account `stflight60106354`, containers `raw`, `processed`, `curated`
- Azure Databricks workspace with a Unity Catalog-enabled project cluster; notebooks use Python, Spark SQL, PySpark, `dbutils`, pandas and matplotlib
- Existing Unity Catalog schema: `dsai3202_databricks.proj_flight60106354`
- Storage permissions for listing/reading raw input and writing processed/curated paths; the instructor provisioned external locations
- External locations: `loc_proj_flight60106354_raw`, `loc_proj_flight60106354_processed`, `loc_proj_flight60106354_curated`
- No credentials should appear in GitHub. Obtain access via instructor/appropriate workspace role.

**Important:** Dataset and cloud access are required to reproduce the notebooks. `pip install -r requirements.txt` on a laptop alone is not sufficient. Avoid enabling unrestricted public storage networking; restore organization-approved firewall restrictions once access is configured.
