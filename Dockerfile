
FROM python:3.11-slim
WORKDIR /app
RUN pip install flask
COPY src/app.py .
CMD ["python", "app.py"]
