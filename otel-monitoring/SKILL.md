---
name: otel-monitoring
description: 'Add observability/monitoring to a service or docker-compose stack. Use when adding tracing, metrics, or logging instrumentation; configuring an OpenTelemetry collector; or wiring up OTEL exporters. Prefers OTLP gRPC (port 4317) over HTTP (port 4318). Handles docker networking via host.docker.internal.'
---

# OpenTelemetry Monitoring

Prefer OpenTelemetry (OTEL) for all observability. Use OTLP gRPC (`4317`) by default — fall back to OTLP HTTP (`4318`) only if the SDK or environment doesn't support gRPC.

## Collector Ports

| Protocol | Port |
|----------|------|
| OTLP gRPC | `4317` |
| OTLP HTTP | `4318` |

---

## Docker: Reaching a Local Collector

When a containerised service needs to export to an OTEL collector running on the host (or in another compose stack), use Docker's `host-gateway` alias — **not** `localhost` or `127.0.0.1`, which resolve to the container itself.

```yaml
services:
  myapp:
    environment:
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://host.docker.internal:4317"
      OTEL_EXPORTER_OTLP_PROTOCOL: "grpc"          # explicit, some SDKs default to http
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

- `host-gateway` is resolved by Docker at runtime to the host's bridge IP.
- The `extra_hosts` entry must be present on **every service** that exports telemetry — it is not inherited.
- If the collector is in the **same compose stack**, use the service name instead:
  ```yaml
  OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector:4317"
  ```
  No `extra_hosts` needed in that case.

---

## Common OTEL Environment Variables

Set these on the instrumented service:

```yaml
environment:
  OTEL_SERVICE_NAME: "my-service"
  OTEL_EXPORTER_OTLP_ENDPOINT: "http://host.docker.internal:4317"
  OTEL_EXPORTER_OTLP_PROTOCOL: "grpc"
  OTEL_TRACES_EXPORTER: "otlp"
  OTEL_METRICS_EXPORTER: "otlp"
  OTEL_LOGS_EXPORTER: "otlp"
```

Only set `OTEL_TRACES_EXPORTER` / `OTEL_METRICS_EXPORTER` / `OTEL_LOGS_EXPORTER` if you want to be explicit — most SDKs default to `otlp` when `OTEL_EXPORTER_OTLP_ENDPOINT` is set.

---

## Adding a Collector to a Compose Stack

If the project doesn't already have a collector, add one:

```yaml
services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.102.0   # pin version
    restart: unless-stopped
    volumes:
      - ./otel-collector-config.yaml:/etc/otelcol-contrib/config.yaml:ro
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP (optional)
    networks:
      - app-net
```

Provide a minimal `otel-collector-config.yaml` alongside the compose file:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

exporters:
  debug:
    verbosity: normal
  # add your backend exporter here (e.g. otlphttp/jaeger, prometheus, etc.)

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [debug]
    metrics:
      receivers: [otlp]
      exporters: [debug]
    logs:
      receivers: [otlp]
      exporters: [debug]
```

Replace the `debug` exporter with the appropriate backend (Jaeger, Grafana, Prometheus, etc.) for production use.

---

## Verification

After wiring up instrumentation, confirm data is flowing:

1. Start the stack: `docker compose up -d`
2. Exercise the service (make a request, trigger an action).
3. Check collector logs for received spans/metrics:
   ```bash
   docker compose logs otel-collector
   ```
   Look for lines like `TracesExporter` or `NumberDataPoints` — absence means the exporter env vars are wrong or the `extra_hosts` entry is missing.
4. If nothing appears, verify the endpoint is reachable from inside the container:
   ```bash
   docker compose exec myapp wget -qO- http://host.docker.internal:4317
   # expect a gRPC or connection-refused response, not "Name or service not known"
   ```

Do not declare monitoring complete until telemetry is confirmed to be received by the collector.

---

## Checklist

- [ ] `OTEL_EXPORTER_OTLP_ENDPOINT` set with correct port (prefer `4317` gRPC)
- [ ] `extra_hosts: ["host.docker.internal:host-gateway"]` on every exporting service (if using host collector)
- [ ] `OTEL_SERVICE_NAME` set to a meaningful name
- [ ] Collector or backend is running and reachable
- [ ] Telemetry confirmed flowing in collector logs
