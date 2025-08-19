# syntax=docker/dockerfile:1

FROM python:3.11

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the source
COPY . .

# Ensure output directory exists
RUN mkdir -p market_data

# Default command
CMD ["python", "crypto_analysis.py"]


