# Production Readiness Checklist (v0.1.0)

## Required before production

* Replace SQLite with Postgres (migrations + connection pooling)
* Add authN/authZ (OIDC/JWT) and service-to-service controls
* Add rate limiting and request tracing (OpenTelemetry)
* Enforce retention policies for logs/artifacts
* Ensure no raw PII leaves controlled boundaries (prompt logging policy)
* Implement monitoring:
  * drift (PSI/KS)
  * performance (precision/recall on chargebacks/labels)
  * alerting + dashboards (Grafana/Datadog)

## LLM Safety Controls

* Agents are optional and do not decide.
* PII redaction is default (`INCLUDE_PII=false`).
* Do not log raw prompts with PII.
