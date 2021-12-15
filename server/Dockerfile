FROM arm32v7/python:3.9.6-alpine
WORKDIR /app
COPY . .

RUN apk add git && \
    python -m pip install --upgrade pip && \
    pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "./app.py"]