# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

# System deps needed by matplotlib/seaborn (fonts) and pyarrow
RUN apt-get update && apt-get install -y --no-install-recommends \
        libfreetype6 \
        libpng16-16 \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Making sure the writable data/report/chart/log directories exist
RUN mkdir -p data/raw data/processed data/reports reports charts logs

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

EXPOSE 8501

# Default: To run the analytics pipeline once (load -> clean -> analyze -> report).
#   docker run -p 8501:8501 momentum-analyzer streamlit run src/dashboard.py --server.address=0.0.0.0
CMD ["python", "src/main.py"]
