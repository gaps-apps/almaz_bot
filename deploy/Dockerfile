FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .

ENV PIP_ROOT_USER_ACTION=ignore

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

CMD ["python", "main.py"]