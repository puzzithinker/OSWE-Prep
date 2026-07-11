FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc \
 && pip install --no-cache-dir flask==3.0.0 psycopg2-binary==2.9.9 \
 && rm -rf /var/lib/apt/lists/*
COPY app/ /app/
RUN mkdir -p /app/static && echo "OSWE{pg_sqli_lab_flag}" > /flag.txt \
 && echo "OSWE{pg_sqli_lab_flag}" > /app/static/flag.txt
ENV FLASK_APP=app.py
EXPOSE 8080
CMD ["python", "app.py"]
