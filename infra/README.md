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
