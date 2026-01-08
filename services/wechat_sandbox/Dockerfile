FROM jlesage/baseimage-gui:debian-11

# 安装必要的依赖
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    python3 \
    python3-pip \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# 复制生产者服务
COPY producer_service/ /app/producer_service/

# 设置工作目录
WORKDIR /app

# 暴露端口
EXPOSE 5800 5900 6789

# 启动脚本
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
