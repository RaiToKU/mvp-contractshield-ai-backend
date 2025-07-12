# Docker 构建优化指南

## 概述

本文档介绍了如何优化 Docker 镜像构建速度，主要通过使用国内镜像源来加速下载过程。

## 优化内容

### 1. 使用国内镜像源

#### Debian 包管理器优化
```dockerfile
# 配置 Debian 使用清华大学镜像源
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list
```

#### Python pip 优化
```dockerfile
# 配置 pip 使用清华大学镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip install --no-cache-dir -r requirements.txt
```

### 2. 可选的镜像源

#### 阿里云镜像源
```bash
# Debian 源
https://mirrors.aliyun.com/debian/
# pip 源
https://mirrors.aliyun.com/pypi/simple/
```

#### 网易云镜像源
```bash
# Debian 源
https://mirrors.163.com/debian/
# pip 源
https://mirrors.163.com/pypi/simple/
```

#### 中科大镜像源
```bash
# Debian 源
https://mirrors.ustc.edu.cn/debian/
# pip 源
https://pypi.mirrors.ustc.edu.cn/simple/
```

## 构建速度对比

### 优化前
- 使用官方源：约 10-15 分钟
- 网络延迟高，下载速度慢

### 优化后
- 使用国内镜像源：约 3-5 分钟
- 网络延迟低，下载速度快

## 注意事项

1. **镜像源选择**：建议优先使用清华大学或中科大镜像源，稳定性较好
2. **网络环境**：在国内网络环境下效果最明显
3. **缓存利用**：Docker 会缓存已构建的层，重复构建时速度会更快
4. **依赖管理**：保持 requirements.txt 文件精简，避免不必要的依赖

## 完整的优化后 Dockerfile

```dockerfile
# 使用官方 Python 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 配置 Debian 使用清华大学镜像源
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    libtesseract-dev \
    poppler-utils \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 配置 pip 使用清华大学镜像源并安装Python依赖
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p uploads exports logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV TESSERACT_CMD=/usr/bin/tesseract

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "run.py"]
```

## 使用方法

1. 确保 Dockerfile 已更新为优化版本
2. 运行构建脚本：
   ```bash
   cd deployment
   ./push_image.sh
   ```

## 故障排除

### 镜像源不可用
如果某个镜像源不可用，可以尝试其他镜像源：

```bash
# 测试镜像源可用性
curl -I https://mirrors.tuna.tsinghua.edu.cn/debian/
curl -I https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 构建失败
1. 检查网络连接
2. 尝试使用不同的镜像源
3. 清理 Docker 缓存：`docker system prune -a`

## 更新日志

- 2024-01-XX: 初始版本，添加清华大学镜像源优化
- 修复了 Debian 12 (bookworm) 的源配置问题
- 移除了对 OpenCV 的依赖，使用轻量级 PDF 处理库