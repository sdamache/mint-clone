FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y curl && \
    pip install -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["python", "app.py"]
