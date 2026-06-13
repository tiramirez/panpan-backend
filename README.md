# panpan-backend

Lambda functions and Terraform infrastructure for the Panpan buying club.

## Structure

```
lambdas/
  api/          # FastAPI app (Mangum adapter) — handles all API Gateway routes
  send-email/   # SQS consumer — saves order to DynamoDB, sends Gmail confirmation
  shared/       # Lambda Layer — shared logger, S3, and DynamoDB utilities
terraform/
  main.tf       # DynamoDB, SQS, S3, IAM, Lambda, API Gateway resources
  variables.tf
  environments/
    dev.tfvars
    prod.tfvars
scripts/
  build.sh      # Builds a lambda zip into dist/
.github/workflows/
  deploy-infra.yml   # Terraform plan + apply on push to develop/prod
  deploy-lambdas.yml # Selective lambda deploy (only changed lambdas)
```

## Local development

```bash
make venv && make install
source .venv/bin/activate
pytest lambdas/lambda_test/test.py
```

## Deployment

Triggered automatically by GitHub Actions on push to `develop` (→ dev) or `prod` (→ prod).

- `deploy-infra.yml` — runs Terraform. Only changed lambdas are built/deployed.
- `deploy-lambdas.yml` — builds and deploys only the lambdas whose source paths changed.

## Secrets

Sensitive variables are stored in **AWS Secrets Manager**, not GitHub secrets.

| Secret name | Used for |
|-------------|----------|
| `panpan/dev/terraform` | dev environment tfvars (e.g. `panpan_gmail_password`) |
| `panpan/prod/terraform` | prod environment tfvars |

Format: JSON blob — `{"panpan_gmail_password": "..."}`.

The GitHub Actions OIDC role requires `secretsmanager:GetSecretValue` on `arn:aws:secretsmanager:us-east-1:<account>:secret:panpan/*`.

To add a new secret variable:
1. Add the key to both Secrets Manager secrets via the AWS console or CLI.
2. Add a corresponding `echo` line in the `Load secrets from Secrets Manager` step in `deploy-infra.yml`.
3. Pass it as a `TF_VAR_*` env var in the Plan and Apply steps.

## Terraform

### Bootstrap (first time only)

The Terraform state bucket must be created manually before `terraform init` can run — this is a one-time step per AWS account:

```bash
aws s3api create-bucket \
  --bucket panpan-terraform-state \
  --region us-east-1

aws s3api put-bucket-versioning \
  --bucket panpan-terraform-state \
  --versioning-configuration Status=Enabled
```

### Usage

```bash
cd terraform
terraform init -backend-config="key=terraform/<workspace>/terraform.tfstate"
terraform workspace select dev   # or prod
terraform plan -var-file=environments/dev.tfvars
terraform apply
```

Non-sensitive variables live in `terraform/environments/{env}.tfvars` (committed). Sensitive variables are injected via `TF_VAR_*` env vars pulled from Secrets Manager in CI.
