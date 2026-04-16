from contextvars import ContextVar

# Set by CorrelationIdMiddleware at the start of each request.
# Read by JsonFormatter so every log line automatically carries the correlation ID
# without needing to pass it through every function signature.
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="-")
