FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
COPY bookings.json /app/database/bookings.json
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]