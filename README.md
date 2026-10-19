# Building a Root Cause Analytics Engine

A Kubernetes Day/CNCF-style talk and reproducible local reference for controlled, evidence-first incident investigation. Prometheus records service signals, Loki stores structured application logs, Grafana correlates both, a read-only MCP server exposes bounded evidence tools, and a local CLI persists an explicit RCA workflow.

The presentation describes a pattern developed while working with a confidential fintech client. This repository is a synthetic learning aid. It contains no client identifiers, production data, internal topology, or incident details.

## What the demo proves

The synthetic request path is `checkout → orders → payments`. A contained ConfigMap fault adds payment latency and intermittent failures. The workflow then:

1. receives a synthetic incident and persists a bounded `±30 minute` plan;
2. collects fixed Prometheus and Loki evidence in parallel;
3. synthesizes an evidence-backed proposal with stated limitations;
4. requires an explicit local operator transition before mitigation;
5. leaves fault removal to the operator;
6. records validation, resolution, and a Markdown RCA draft for review.

The demo has no LLM, shell tool, arbitrary PromQL/LogQL input, Kubernetes mutation path, external chat integration, or autonomous remediation.

## Prerequisites

- Docker Desktop or another working Docker daemon
- `kind`, `kubectl`, `make`, and Node.js 18+

On macOS:

```sh
brew install kind kubectl
```

## Start the stack

```sh
make up
make grafana
```

Open [http://localhost:3001](http://localhost:3001). The disposable local Grafana instance permits anonymous viewer access.

The dashboard shows request rate, error ratio, p95 latency, and structured Loki error logs. In separate terminals, expose the source APIs used by the MCP evidence gateway:

```sh
make prometheus
make loki
PROMETHEUS_URL=http://localhost:9090 LOKI_URL=http://localhost:3100 \
  node demo/mcp/server.js
```

The MCP server exposes fixed read-only tools. Every request needs an ISO-8601 `start` and `end` within 60 minutes:

```text
alert_context(start, end)
service_health(service, start, end)
dependency_health(service, start, end)
top_error_signatures(service, start, end)
```

The server accepts only `checkout`, `orders`, and `payments`; it never accepts arbitrary PromQL, LogQL, URLs, shell commands, or Kubernetes commands.

## Exercise the controlled RCA workflow

Allow traffic, recording rules, and logs to accumulate for about two minutes. Trigger the synthetic failure, wait about one minute for the alert, then create an incident:

```sh
make fault-on
(cd demo/rca && go run ./cmd/rca create)
```

The command prints an incident ID. Use it in the following sequence:

```sh
(cd demo/rca && go run ./cmd/rca investigate <incident-id>)
(cd demo/rca && go run ./cmd/rca status <incident-id>)
(cd demo/rca && go run ./cmd/rca approve-mitigation <incident-id> \
  --note 'operator will disable the contained payment fault')
make fault-off
(cd demo/rca && go run ./cmd/rca validate <incident-id>)
(cd demo/rca && go run ./cmd/rca resolve <incident-id>)
(cd demo/rca && go run ./cmd/rca draft-rca <incident-id>)
```

`approve-mitigation` records a human decision only. It cannot mutate the cluster. `make fault-off` remains a separate, explicit operator action. The final command prints the review-only draft path, normally `demo/rca/state/<incident-id>/rca-draft.md`.

To investigate again, an operator must make the explicit transition and run collection again:

```sh
(cd demo/rca && go run ./cmd/rca reinvestigate <incident-id>)
(cd demo/rca && go run ./cmd/rca investigate <incident-id>)
```

## Verify

```sh
make test
kubectl kustomize demo >/dev/null
```

After `make up`, `make verify` waits for Prometheus, Grafana, Loki, and Promtail. For a live acceptance check, confirm:

1. Grafana's `Root Cause Analytics Demo` dashboard contains both Prometheus metrics and Loki structured error logs.
2. The payment fault raises the payment error ratio and p95 latency, with downstream effects in orders and checkout.
3. `investigate` records Prometheus and Loki evidence with a bounded range, query template reference, source, and limitations.
4. Resolution is rejected before the explicit manual-mitigation and validation transitions.
5. The generated Markdown RCA is a draft and records the evidence, assessment, human action, and review boundary.
6. The MCP tool list and CLI contain no mutation command.

## Local limitations

The local environment deliberately uses static service allowlists, local JSON incident files, anonymous Grafana viewer access, and namespace-local Kubernetes RBAC. It does not model a production identity provider, isolated per-worker credentials, secret management, retention/redaction policy, Slack or Telegram callbacks, durable database storage, traces, or document publishing.

Treat Grafana MCP as a bounded evidence interface, not a complete authorization or incident-management system. Metrics and logs support correlation and hypothesis formation. They do not establish causation or authorize remediation.

## Presentation

The slide source and speaker notes live at [`slides/deck.md`](slides/deck.md). Render it with the instructions in [`slides/README.md`](slides/README.md).
