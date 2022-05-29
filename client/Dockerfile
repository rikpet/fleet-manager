FROM arm32v6/python:3.9.6-alpine
WORKDIR /app
COPY . .

RUN mkdir share



RUN apk add git gcc python3-dev gpgme-dev libc-dev && \
    python -m pip install --upgrade pip && \
    pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "./app.py"]