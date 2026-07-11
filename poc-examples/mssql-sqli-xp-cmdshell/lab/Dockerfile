FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir flask==3.0.0 pymssql==2.2.11
COPY app/ /app/
RUN echo "OSWE{mssql_sqli_lab_flag}" > /flag.txt
EXPOSE 8080
CMD ["python", "app.py"]
