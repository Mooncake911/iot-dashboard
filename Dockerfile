FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv for faster dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application files
COPY application.yml /app/application.yml
COPY app.py /app/app.py
COPY dashboard /app/dashboard

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
