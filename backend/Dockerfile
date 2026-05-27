# LocateAnything-3B backend — CUDA runtime + PyTorch + FastAPI.
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LA_DATA_DIR=/data \
    HF_HOME=/hf_cache

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev build-essential git \
    libgl1 libglib2.0-0 \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# PyTorch for CUDA 12.4 (installed separately from the CUDA wheel index, per
# the model card). Pinning here keeps image builds reproducible.
RUN pip3 install --upgrade pip \
    && pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu124

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
