FROM python:3.12.4-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

RUN "ls"

CMD ["python", "src/main.py"]