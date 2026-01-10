FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    x11-apps \
    xvfb \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    libnotify4 \
    libnss3 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    libatspi2.0-0 \
    libappindicator3-1 \
    libsecret-1-0 \
    libgbm1 \
    wget \
    tigervnc-standalone-server \
    tigervnc-common \
    tigervnc-tools \
    novnc \
    websockify \
    x11vnc \
    fluxbox 
#    \
#    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /root/.vnc && \
    chmod 700 /root/.vnc

ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

CMD ["bash", "start.sh"]
