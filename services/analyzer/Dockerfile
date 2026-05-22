FROM python:3.11-slim
WORKDIR /app
COPY app ./app
ENV ANALYZER_HOST=0.0.0.0
ENV ANALYZER_PORT=8001
EXPOSE 8001
CMD ["python", "app/main.py"]

