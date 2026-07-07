# AWS Deployment

This Pulumi project deploys the app to AWS as a single containerized service:

- `ECR` for the application image
- `ECS Fargate` for running the app
- `Application Load Balancer` for public HTTP access
- `EFS` for persistent SQLite and editable prompt/source config files
- `CloudWatch Logs` for container logs
- `Secrets Manager` for API keys

The container builds the React app and serves it through FastAPI, so the deployment exposes one public URL.

## Architecture

- The Docker image is built from the repository root.
- The FastAPI app serves the built frontend from `web/dist`.
- SQLite lives at `/app/data/willbe.db` on the EFS mount.
- Prompt and preferred-source config are persisted to:
  - `/app/data/prompts.yaml`
  - `/app/data/preferred_sources.yaml`

This keeps the in-app prompt/source editors working across task restarts.

## Prerequisites

- AWS credentials configured for Pulumi
- A Pulumi backend selected (`pulumi login ...`)
- Node.js 20+
- Docker running locally

## Deploy user

Deployments use a dedicated IAM user instead of an admin/root profile:

| Item | Value |
|------|-------|
| IAM user | `willbe-trends-pulumi-deploy` |
| Local AWS CLI profile | `willbe-trends-deploy` |
| AWS account | `247377984913` |
| Region | `ap-southeast-1` |
| Pulumi state bucket | `s3://willbe-trends-pulumi-state-247377984913-ap-southeast-1` |
| Pulumi secrets KMS key | `arn:aws:kms:ap-southeast-1:247377984913:key/c58ae16d-3e37-4a11-bb0e-eb3934939d4c` |

Use this profile for all infra commands:

```bash
export AWS_PROFILE=willbe-trends-deploy
export AWS_REGION=ap-southeast-1

cd infra
pulumi login "s3://willbe-trends-pulumi-state-247377984913-ap-southeast-1"
pulumi stack select dev
pulumi up
```

Verify the profile:

```bash
aws --profile willbe-trends-deploy sts get-caller-identity
```

### Attached managed policies

These AWS managed policies were attached so Pulumi can provision and update the stack:

- `AmazonEC2FullAccess` — VPC, subnets, security groups
- `AmazonECS_FullAccess` — ECS cluster, services, task definitions
- `AmazonEC2ContainerRegistryFullAccess` — ECR repository and image push
- `AmazonElasticFileSystemFullAccess` — EFS for persistent app data
- `ElasticLoadBalancingFullAccess` — ALB, listeners, target groups
- `CloudWatchLogsFullAccess` — container log groups
- `SecretsManagerReadWrite` — OpenAI / site-auth secrets for ECS tasks
- `IAMFullAccess` — ECS task and execution roles created by the stack
- `AmazonRoute53FullAccess` — DNS validation and alias record for the custom domain
- `AWSCertificateManagerFullAccess` — HTTPS certificate for the custom domain

### Inline policies

Two user-specific inline policies were added on top of the managed policies:

- `WillbeTrendsPulumiStateBucketAccess` — read/write the Pulumi state bucket only
- `WillbeTrendsPulumiSecretsKmsAccess` — encrypt/decrypt stack secrets with the Pulumi KMS key

### Notes

- Create and manage this user with an admin profile such as `willbe-chinhnguyen`; day-to-day deploys should use `willbe-trends-deploy`.
- The managed policies are broad by design for Pulumi. Tightening them later would mean replacing `IAMFullAccess` and the `*FullAccess` policies with a custom least-privilege policy scoped to this stack.
- Programmatic access keys for `willbe-trends-pulumi-deploy` live in your local `~/.aws/credentials` under the `willbe-trends-deploy` profile. Rotate them from IAM if needed.

## Install

```bash
cd infra
npm install
pulumi stack init dev
```

## Configure

Required for hosted inference:

```bash
pulumi config set llmProvider openai
pulumi config set --secret openaiApiKey YOUR_KEY
```

Optional:

```bash
pulumi config set searchProvider duckduckgo
pulumi config set domainName trending-research.wilbi.fi
pulumi config set hostedZoneName wilbi.fi
pulumi config set desiredCount 1
pulumi config set containerCpu 512
pulumi config set containerMemory 1024
pulumi config set openaiModel gpt-4o-mini
pulumi config set anthropicModel claude-sonnet-4-20250514
pulumi config set imageSearchEnabled true
pulumi config set tavilyEnabled true
pulumi config set --secret tavilyApiKey YOUR_TAVILY_KEY
pulumi config set --secret anthropicApiKey YOUR_ANTHROPIC_KEY
pulumi config set httpAuthUser willbe
pulumi config set --secret httpAuthPassword YOUR_SITE_PASSWORD
```

## Deploy

```bash
cd infra
pulumi up
```

Pulumi outputs the public ALB URL after deployment.

## Notes

- This deploy shape is best for the current codebase because it avoids rewriting the app for RDS/S3 hosting.
- `ollama` is not a good fit for this AWS setup unless you add your own model-serving infrastructure.
- The stack provisions an ACM certificate with DNS validation and creates a Route53 alias record for the configured domain.
- Set `httpAuthUser` and `httpAuthPassword` to enable HTTP basic auth on the public site. `/api/health` stays open for load balancer checks.
