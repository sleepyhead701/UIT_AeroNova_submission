# BASE IMAGE theo yêu cầu BTC
FROM nvidia/cuda:12.2.0-devel-ubuntu20.04

# Tránh interactive prompt khi cài apt
ENV DEBIAN_FRONTEND=noninteractive

# Cài đặt Python và pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    build-essential \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Link python3 -> python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Thiết lập thư mục làm việc
WORKDIR /code

# Copy requirements và cài đặt trước để tận dụng cache layer
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# (Tùy chọn) Pre-download model sentence-transformers để chạy offline
# RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('keepitreal/vietnamese-sbert')"

# Copy toàn bộ source code
COPY . .

# Cấp quyền chạy cho script
RUN dos2unix inference.sh && chmod +x inference.sh

# Lệnh mặc định
CMD ["bash", "inference.sh"]