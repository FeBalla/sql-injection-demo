#!/usr/bin/env bash
# Least-privilege GCP setup for the Injection Lab BigQuery backend.
#
# Creates:
#   - a dataset holding the single demo table `customers`
#   - a service account with roles/bigquery.dataEditor on that dataset only
#     and roles/bigquery.jobUser on the project (needed to run queries)
#   - a roles/iam.serviceAccountTokenCreator binding on that service account
#     for you, so you can impersonate it locally without a key file
#
# Usage:
#   GCP_PROJECT_ID=my-project \
#   GCP_IMPERSONATOR=user:me@example.com \
#   ./infra/gcp/setup.sh
#
# Optional: GCP_ACCOUNT (gcloud account to run as), BQ_DATASET, BQ_LOCATION, SA_NAME.
# The script is idempotent: re-running it skips anything that already exists.
set -euo pipefail

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID to the project to use}"
: "${GCP_IMPERSONATOR:?Set GCP_IMPERSONATOR to the member that may impersonate the service account, e.g. user:me@example.com}"
BQ_DATASET="${BQ_DATASET:-injection_lab}"
BQ_LOCATION="${BQ_LOCATION:-US}"
SA_NAME="${SA_NAME:-injection-lab-api}"
SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Scope gcloud and bq to this project/account for this process only,
# without touching the caller's gcloud configuration.
export CLOUDSDK_CORE_PROJECT="$GCP_PROJECT_ID"
if [[ -n "${GCP_ACCOUNT:-}" ]]; then
  export CLOUDSDK_CORE_ACCOUNT="$GCP_ACCOUNT"
fi

# New service accounts take a few seconds to become visible to IAM.
retry() {
  local attempt
  for attempt in 1 2 3 4 5 6; do
    if "$@"; then return 0; fi
    echo "  retrying in $((attempt * 5))s..." >&2
    sleep $((attempt * 5))
  done
  return 1
}

echo "==> Enabling BigQuery and IAM Credentials APIs"
gcloud services enable bigquery.googleapis.com iamcredentials.googleapis.com

echo "==> Dataset ${BQ_DATASET} (${BQ_LOCATION})"
if ! bq --project_id="$GCP_PROJECT_ID" show --dataset "${GCP_PROJECT_ID}:${BQ_DATASET}" >/dev/null 2>&1; then
  bq --project_id="$GCP_PROJECT_ID" --location="$BQ_LOCATION" mk --dataset \
    --description="Injection Lab demo data" "${GCP_PROJECT_ID}:${BQ_DATASET}"
fi

echo "==> Table ${BQ_DATASET}.customers"
if ! bq --project_id="$GCP_PROJECT_ID" show "${GCP_PROJECT_ID}:${BQ_DATASET}.customers" >/dev/null 2>&1; then
  bq --project_id="$GCP_PROJECT_ID" mk --table "${GCP_PROJECT_ID}:${BQ_DATASET}.customers" \
    id:INTEGER,name:STRING,email:STRING,country:STRING,plan:STRING
fi

echo "==> Service account ${SA_EMAIL}"
if ! gcloud iam service-accounts describe "$SA_EMAIL" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$SA_NAME" \
    --display-name="Injection Lab API" \
    --description="Runs Injection Lab queries against the demo dataset only"
fi

echo "==> roles/bigquery.dataEditor on dataset ${BQ_DATASET} only"
# BigQuery DCL grants the role on this dataset (schema) and nothing else.
retry bq --project_id="$GCP_PROJECT_ID" --location="$BQ_LOCATION" query --nouse_legacy_sql --quiet \
  "GRANT \`roles/bigquery.dataEditor\` ON SCHEMA \`${GCP_PROJECT_ID}.${BQ_DATASET}\` TO \"serviceAccount:${SA_EMAIL}\"" >/dev/null

echo "==> roles/bigquery.jobUser on project ${GCP_PROJECT_ID}"
retry gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.jobUser" \
  --condition=None >/dev/null

echo "==> ${GCP_IMPERSONATOR} may impersonate ${SA_EMAIL}"
retry gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --member="$GCP_IMPERSONATOR" \
  --role="roles/iam.serviceAccountTokenCreator" >/dev/null

cat <<EOF

Done. Create local credentials that impersonate the service account.
They go to a separate gcloud config dir, so your default ADC is left alone:

  CLOUDSDK_CONFIG="\$HOME/.config/gcloud-injection-lab" \\
    gcloud auth application-default login --impersonate-service-account=${SA_EMAIL}

Then set GCP_PROJECT_ID and BQ_DATASET in .env and enable the BigQuery compose
override (see README).
EOF
