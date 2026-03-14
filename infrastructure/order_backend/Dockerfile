FROM python:3.11-slim
WORKDIR /app
RUN pip install fastapi uvicorn requests opentelemetry-distro opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-requests
COPY main.py .
EXPOSE 8082
CMD ["opentelemetry-instrument", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]
