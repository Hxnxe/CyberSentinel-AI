# GitHub Actions Reports

CyberSentinel AI can generate a one-shot Markdown report in GitHub Actions and store it as a workflow artifact. The workflow does not commit generated reports back to the repository.

## Workflow

The workflow file is:

```text
.github/workflows/generate-report.yml
```

It supports:

- daily scheduled runs at `01:00 UTC`;
- manual runs through **Actions -> Generate Security Report -> Run workflow**;
- artifact upload with 14-day retention.

## Secrets

The workflow can run with the built-in `GITHUB_TOKEN`, but a personal token usually has better API limits for GitHub search.

Optional repository secrets:

| Secret | Purpose |
| --- | --- |
| `REPORT_GITHUB_TOKEN` | Single GitHub token used by the report workflow. |
| `REPORT_GITHUB_TOKENS` | JSON array of GitHub tokens, for example `["token1","token2"]`. |

Do not store tokens in workflow files or commit them to the repository.

## Manual inputs

| Input | Default | Description |
| --- | --- | --- |
| `max_items` | `20` | Maximum candidates per report section. |
| `keyword_limit` | `5` | Number of default keywords to query when no override is supplied. |
| `keywords` | empty | Optional comma-separated keyword override, for example `rce,poc,cloud security`. |
| `include_cve` | `true` | Include CVE candidate collection. |
| `include_repositories` | `true` | Include repository candidate collection. |

## Local dry run

```bash
python scripts/generate_report.py \
  --output artifacts/github-security-report.md \
  --max-items 20 \
  --keyword-limit 5
```

The generated report is ignored by git:

```text
artifacts/
github-actions-report.db
```

## Artifact download

After the workflow finishes:

1. Open the workflow run in GitHub Actions.
2. Download the `cybersentinel-ai-report-<run-number>` artifact.
3. Open `github-security-report.md`.
