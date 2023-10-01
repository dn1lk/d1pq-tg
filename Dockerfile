FROM python:3.11-alpine as builder
LABEL maintainer="dn1lk <sh.dn1lk@gmail.com>"

# Build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools \
 && pip install --no-cache-dir -r requirements.txt


# Stage
FROM python:3.11-alpine
COPY --from=builder /opt/venv /opt/venv

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /bot
COPY bot .
CMD ["python", "__main__.py"]