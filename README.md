# autonomous-revenue-factories
Self-running software factories using Claude Code, MCP integrations, and scheduled loops. Each factory continuously ingests market signals, builds and tests revenue-generating outputs self-improves from telemetry, and escalates to a human operator only for capital deployment or final launch approval.

## Status

Research and design only. Nothing in this repository has been built or run yet.

- [`RESEARCH_REPORT.md`](RESEARCH_REPORT.md): what is verifiably earning money, seven factory models ranked by portfolio expected value (consumer app portfolio first), a review of demand-testing services, a tooling matrix with verified prices and MCP status, and an audit of the operator environment.
- [`ARCHITECTURE.md`](ARCHITECTURE.md): the shared runtime, control plane, escalation protocol and build sequence.
- [`factories/`](factories/): one self-contained blueprint per factory (`FACTORY_SPEC.md`, `CLAUDE.md`, `ESCALATION.md`, `budget.yaml`, `skills/`, `agents/`), plus shared conventions in [`factories/_shared/`](factories/_shared/).
