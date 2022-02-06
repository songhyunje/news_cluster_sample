FROM pytorch/pytorch:1.10.0-cuda11.3-cudnn8-devel
ENV PYTHON_VERSION=3.10.0
RUN apt-get update && apt-get install -y --no-install-recommends \
         build-essential \
         locales \
         sudo \
         cmake \
         screen \
         git \
         curl \
         vim \
         tree \
         ca-certificates \
         libjpeg-dev \
         openssh-server \
         libopenblas-dev \
         libomp-dev \
         libpng-dev &&\
     rm -rf /var/lib/apt/lists/*

RUN locale-gen ko_KR.UTF-8
ENV LANG=ko.KR.utf8 TZ=Asia/Seoul
ENV LC_ALL=ko_KR.utf8

RUN mkdir -p /workspace/simple

WORKDIR /workspace/simple
COPY requirements.txt /workspace/simple
RUN pip install --no-cache-dir -r requirements.txt

COPY . /workspace/simple
