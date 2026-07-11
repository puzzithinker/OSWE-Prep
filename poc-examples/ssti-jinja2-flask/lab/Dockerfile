FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir flask==3.0.0
COPY app/ /app/
RUN echo "OSWE{ssti_jinja2_lab_flag}" > /flag.txt
ENV FLASK_APP=app.py
EXPOSE 5000
CMD ["python", "app.py"]
