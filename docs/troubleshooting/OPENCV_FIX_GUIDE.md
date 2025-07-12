# OpenCV 依赖问题修复指南

## 问题描述

运行容器时出现以下错误：
```
ImportError: libGL.so.1: cannot open shared object file: No such file or directory
```

这是因为 `pdf2docx` 库依赖 `cv2` (OpenCV)，而 OpenCV 需要图形库支持。

## 解决方案

### 1. 已修复的文件

#### Dockerfile 修改
已在 `deployment/Dockerfile` 中添加了必要的系统依赖：

```dockerfile
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
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*
```

#### requirements.txt 修改
已在 `requirements.txt` 中添加了 OpenCV 无头版本：

```
opencv-python-headless==4.8.1.78
```

### 2. 重新构建镜像

执行以下命令重新构建镜像：

```bash
cd deployment
./push_image.sh
```

### 3. 验证修复

构建完成后，可以通过以下方式验证：

```bash
# 运行容器测试
docker run --rm contractshield-ai:latest python -c "import cv2; print('OpenCV 导入成功')"
```

### 4. 关键依赖说明

- **libgl1-mesa-glx**: OpenGL 库，OpenCV 需要
- **libglib2.0-0**: GLib 库
- **libsm6, libxext6, libxrender-dev**: X11 相关库
- **libgomp1**: OpenMP 库，用于并行计算
- **opencv-python-headless**: 无头版本的 OpenCV，适合服务器环境

### 5. 替代方案

如果仍然遇到问题，可以考虑：

1. **移除 pdf2docx 依赖**：如果不需要 PDF 转 DOCX 功能
2. **使用其他 PDF 处理库**：如 PyPDF2、pdfplumber 等
3. **使用完整的 Ubuntu 基础镜像**：而不是 slim 版本

### 6. 测试命令

```bash
# 测试 OpenCV 导入
docker run --rm contractshield-ai:latest python -c "
import cv2
from pdf2docx import Converter
print('所有依赖导入成功')
"
```

## 注意事项

- 添加这些依赖会增加镜像大小（约 100-200MB）
- 如果不需要 PDF 转 DOCX 功能，建议移除 pdf2docx 依赖以减小镜像大小
- opencv-python-headless 比完整版 opencv-python 更适合服务器环境