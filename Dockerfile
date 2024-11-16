# Build stage
FROM python:3.12-alpine AS builder
LABEL maintainer="dn1lk <sh.dn1lk@gmail.com>"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.12-alpine

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/opt/venv/lib/python3.12/site-packages:$PYTHONPATH"

WORKDIR /bot
COPY bot .

CMD ["python", "-O", "main.py"]