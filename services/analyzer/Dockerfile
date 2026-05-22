FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV ANALYZER_HOST=0.0.0.0
ENV ANALYZER_PORT=8001
EXPOSE 8001
CMD ["python", "-m", "app.main"]
