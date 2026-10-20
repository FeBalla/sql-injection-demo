# BigQuery (optional)

By default the demo runs against Postgres only. These steps add BigQuery as a second database.

1. **Create the GCP resources.** You need the `gcloud` and `bq` CLIs and a project where you can manage IAM:

   ```bash
   GCP_PROJECT_ID=your-project \
   GCP_IMPERSONATOR=user:you@example.com \
   ./infra/gcp/setup.sh
   ```

   The script is idempotent. It enables the BigQuery and IAM Credentials APIs, creates the `injection_lab` dataset and the `customers` table, and creates the `injection-lab-api` service account with the roles described in [Blast radius](architecture.md#blast-radius). It also lets you impersonate that account. Optional variables: `GCP_ACCOUNT`, `BQ_DATASET`, `BQ_LOCATION`, `SA_NAME`.

2. **Create local credentials that impersonate the service account.** They go to a separate gcloud config directory, so your default ADC is not touched:

   ```bash
   CLOUDSDK_CONFIG="$HOME/.config/gcloud-injection-lab" \
     gcloud auth application-default login \
     --impersonate-service-account=injection-lab-api@your-project.iam.gserviceaccount.com
   ```

3. **Enable it in `.env`:**

   ```bash
   COMPOSE_FILE=docker-compose.yml:docker-compose.bigquery.yml
   GCP_PROJECT_ID=your-project
   BQ_DATASET=injection_lab
   GCP_ADC_FILE=/absolute/path/to/.config/gcloud-injection-lab/application_default_credentials.json
   ```

   `docker-compose.bigquery.yml` mounts that file read-only into the API container. Restart with `make up`. On first start the API seeds the BigQuery table if it is empty.
