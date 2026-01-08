#!/bin/bash

# 启动Xvfb虚拟显示
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# 启动noVNC
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf &

# 启动生产者服务
cd /app/producer_service
python3 main.py
