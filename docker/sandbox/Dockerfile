FROM wechat-base:latest

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

COPY services/wechat_sandbox/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY services/wechat_sandbox /app/services

COPY services/wechat_sandbox/config.yaml /app/config.yaml

COPY services/wechat_sandbox/app /app/app

COPY services/wechat_sandbox/producer_service /app/producer_service

COPY services/wechat_sandbox/utils /app/utils

COPY services/wechat_sandbox/start_service.py /app/

COPY services/wechat_sandbox/main.py /app/

EXPOSE 8000

CMD ["python", "/app/start_service.py"]
