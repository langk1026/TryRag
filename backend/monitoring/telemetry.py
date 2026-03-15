from backend.core.config import config
from backend.core.logger import setup_logger

logger = setup_logger(__name__)

_tracer = None


def configure_telemetry():
    global _tracer

    if not config.telemetry_enabled:
        logger.info("Telemetry disabled by configuration")
        return None

    if _tracer is not None:
        return _tracer

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        current_provider = trace.get_tracer_provider()
        if isinstance(current_provider, TracerProvider):
            _tracer = trace.get_tracer(config.telemetry_service_name)
            logger.debug("Telemetry provider already configured; reusing existing tracer")
            return _tracer

        resource = Resource.create({"service.name": config.telemetry_service_name})
        provider = TracerProvider(resource=resource)

        otlp_exporter = OTLPSpanExporter(endpoint=config.telemetry_otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        if config.telemetry_console_export:
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(config.telemetry_service_name)

        logger.info(f"Telemetry configured for service: {config.telemetry_service_name}")
        return _tracer
    except Exception as e:
        logger.warning(f"Telemetry setup failed: {str(e)}")
        _tracer = None
        return None


def get_tracer(name="tryrag"):
    try:
        from opentelemetry import trace
        return _tracer or trace.get_tracer(name)
    except Exception:
        return None
