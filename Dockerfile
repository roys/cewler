FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser && \
  chown -R appuser:appuser /app

COPY --chown=appuser:appuser . .

USER appuser

RUN pip install --user .
ENV PATH="/home/appuser/.local/bin:$PATH"
ENTRYPOINT ["cewler"]
