import os

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader


def setup_otel(app):
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
        reader = PeriodicExportingMetricReader(exporter)
        provider = MeterProvider(metric_readers=[reader])
        metrics.set_meter_provider(provider)
    FastAPIInstrumentor.instrument_app(app)


meter = metrics.get_meter("workman")
brief_requests = meter.create_counter("workman.brief.requests")
completion_rejections = meter.create_counter("workman.completion.rejections")
notes_surfaced = meter.create_histogram("workman.notes.surfaced_per_brief")
embedding_refreshes = meter.create_counter("workman.embeddings.refresh_triggers")
issues_created = meter.create_counter("workman.issues.created")
task_next_calls = meter.create_counter("workman.task.next_calls")
tooldocs_reindex = meter.create_counter("workman.tooldocs.reindex")
