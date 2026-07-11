FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir flask==3.0.0 lxml==5.1.0
COPY app/ /app/
RUN echo "OSWE{xxe_lab_flag}" > /flag.txt
EXPOSE 80
CMD ["python", "app.py"]
