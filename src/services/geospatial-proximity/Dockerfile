FROM python:3.11-slim

WORKDIR /app

COPY src/services/geospatial-proximity/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src/libraries ./src/libraries
COPY src/services/geospatial-proximity ./src/services/geospatial-proximity
ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "main:app", "--app-dir", "/app/src/services/geospatial-proximity", "--host", "0.0.0.0", "--port", "8000"]
