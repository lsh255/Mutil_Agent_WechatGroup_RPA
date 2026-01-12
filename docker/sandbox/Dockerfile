# ============================================================
# 微信沙盒基础镜像 Dockerfile
# ============================================================
#
# 用途：构建生产环境和默认环境使用的微信沙盒镜像
#
# 功能特性：
#   - VNC 服务器（端口 5900）
#   - noVNC Web 访问（端口 6080）
#   - 微信 Linux 版本（4.1.13）
#   - Python 3.10 + FastAPI
#   - 双生产者架构（视觉方案）
#
# 分层构建策略（优化缓存和构建速度）：
#   Layer 1: 基础系统工具（几乎不变）
#   Layer 2: 桌面环境（VNC + noVNC + X11 + Fluxbox）
#   Layer 3: WeChat 基础依赖
#   Layer 4: 中文字体
#   Layer 5: WeChat 应用安装
#   Layer 6: 依赖补丁（高频变动）
#   Layer 7: Python 环境和依赖
#   Layer 8: 应用代码和配置
#
# 生成镜像：wechat_sandbox:latest
#
# 使用场景：
#   - 生产环境部署
#   - 默认开发环境
#   - 多实例部署（docker-compose.multi.yml）
#
# 不包含：
#   - AT-SPI 辅助功能支持（详见 Dockerfile.test）
#   - 调试工具（Accerciser 等）
#
# 如果需要 AT-SPI 支持，请使用 Dockerfile.test 构建
#
# ============================================================
FROM ubuntu:22.04

# 设置工作目录为 /app
WORKDIR /app

# 设置非交互模式，避免安装时弹出提示
ENV DEBIAN_FRONTEND=noninteractive
# 设置虚拟显示器编号
ENV DISPLAY=:99
# 禁用 Python 输出缓冲，使日志实时显示
ENV PYTHONUNBUFFERED=1

# =====================================================
# 层 1：基础系统工具（几乎不变）
# =====================================================
# 更新包列表并安装基础工具
RUN apt-get update && apt-get install -y --fix-missing \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# =====================================================
# 层 2：桌面环境（VNC + noVNC + X11 + Fluxbox）
# =====================================================
# 更新包列表并安装桌面环境
RUN apt-get update && apt-get install -y --fix-missing \
    xvfb \
    x11-apps \
    fluxbox \
    tigervnc-standalone-server \
    tigervnc-common \
    tigervnc-tools \
    novnc \
    websockify \
    x11vnc \
    && rm -rf /var/lib/apt/lists/*

# =====================================================
# 层 3：WeChat 基础依赖（GUI 库 + 多媒体库）
# =====================================================
# 更新包列表并安装 WeChat 依赖
RUN apt-get update && apt-get install -y --fix-missing \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
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
    libdbus-1-3 \
    libasound2 \
    libpulse0 \
    libpci3 \
    libpci-dev \
    libatomic1 \
    desktop-file-utils \
    && rm -rf /var/lib/apt/lists/*

# =====================================================
# 层 4：字体支持
# =====================================================
# 更新包列表并安装中文字体
RUN apt-get update && apt-get install -y --fix-missing \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# =====================================================
# 层 5：复制并安装本地字体包
# =====================================================
# 复制本地 Noto CJK 字体包到临时目录
COPY build/fonts-noto-cjk_20240730+repack1-1_all.deb /tmp/
# 安装 Noto CJK 字体包
RUN dpkg -i /tmp/fonts-noto-cjk_20240730+repack1-1_all.deb

# =====================================================
# 层 6：WeChat 应用安装
# =====================================================
# 复制本地 WeChat 安装包到临时目录
COPY build/WeChatLinux_x86_64.deb /tmp/
# 强制安装 WeChat（忽略依赖错误）并修复缺失依赖
RUN dpkg --force-depends -i /tmp/WeChatLinux_x86_64.deb && \
    apt-get install -y -f

# =====================================================
# 层 7：依赖补丁层（后续发现缺失依赖可在此添加）
# =====================================================
# 更新包列表并安装补丁依赖
RUN apt-get update && apt-get install -y --fix-missing \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    && rm -rf /var/lib/apt/lists/*

# =====================================================
# 层 8：Python 环境（可选，如需 Python 功能）
# =====================================================
# 更新包列表并安装 Python
RUN apt-get update && apt-get install -y --fix-missing \
    python3 \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# =====================================================
# 层 9：配置与启动脚本
# =====================================================
# 创建 VNC 配置目录并设置权限
RUN mkdir -p /root/.vnc && \
    chmod 700 /root/.vnc

# 复制Python应用代码到容器
COPY services/wechat_sandbox /app/

# 安装Python依赖
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# 创建媒体和日志目录
RUN mkdir -p /app/media /app/logs

# 复制启动脚本到容器
COPY docker/scripts/common/start_wechat.sh /app/
# 设置启动脚本可执行权限
RUN chmod +x /app/start_wechat.sh

# 暴露 noVNC (6080) 和 VNC (5900) 端口
EXPOSE 6080 5900

# 容器启动时执行启动脚本
CMD ["/app/start_wechat.sh"]
