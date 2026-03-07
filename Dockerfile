
FROM python:3.11-slim
RUN useradd -u 1000 -m myuser
WORKDIR /app
RUN pip install flask
COPY src/app.py .
RUN chown -R 1000:1000 /app
USER 1000
CMD ["python", "app.py"]
