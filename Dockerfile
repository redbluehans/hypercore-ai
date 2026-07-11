FROM python:3.12-slim
WORKDIR /app
COPY core ./core
COPY runtime ./runtime
COPY scheduler ./scheduler
COPY memory ./memory
COPY communication ./communication
COPY marketplace ./marketplace
COPY database ./database
COPY production ./production
ENV PYTHONPATH=/app/core:/app/runtime:/app/scheduler:/app/memory:/app/communication:/app/database
RUN useradd -r -u 1001 hypercore && chown -R hypercore:hypercore /app
USER hypercore
EXPOSE 8080
CMD ["python3", "production/main_v2.py"]

# Producción real (Go): ver docs/architecture.txt Sec.5
