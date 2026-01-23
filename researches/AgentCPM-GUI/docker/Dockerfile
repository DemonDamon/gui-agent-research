FROM b66ypcgaicisp01-f8a759e8.ecis.guangzhou-2.cmecloud.cn/prod/unsloth:latest

USER root
ENV DEBIAN_FRONTEND=noninteractive

# 替换为清华源（可选）
RUN sed -i 's|http://[^ ]*\.ubuntu\.com|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list && \
    sed -i 's|http://security\.ubuntu\.com|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list

# 安装 nvcc 编译器（来自 Ubuntu 官方源，与系统兼容）
RUN apt update && \
    apt install -y --no-install-recommends nvidia-cuda-dev nvidia-cuda-toolkit && \
    apt clean && rm -rf /var/lib/apt/lists/*

# 创建 /usr/local/cuda 目录结构并设置符号链接
# deepspeed 期望 CUDA 在 /usr/local/cuda/ 路径下
RUN mkdir -p /usr/local/cuda/bin && \
    mkdir -p /usr/local/cuda/include && \
    mkdir -p /usr/local/cuda/lib64 && \
    ln -sf /usr/bin/nvcc /usr/local/cuda/bin/nvcc && \
    ln -sf /usr/include/cuda.h /usr/local/cuda/include/cuda.h && \
    ln -sf /usr/include/cuda_runtime.h /usr/local/cuda/include/cuda_runtime.h 2>/dev/null || true && \
    find /usr/lib -name "libcudart.so*" -exec ln -sf {} /usr/local/cuda/lib64/ \; 2>/dev/null || true && \
    find /usr/lib -name "libcublas.so*" -exec ln -sf {} /usr/local/cuda/lib64/ \; 2>/dev/null || true && \
    find /usr/lib -name "libcurand.so*" -exec ln -sf {} /usr/local/cuda/lib64/ \; 2>/dev/null || true && \
    find /usr/lib -name "libcusolver.so*" -exec ln -sf {} /usr/local/cuda/lib64/ \; 2>/dev/null || true && \
    find /usr/lib -name "libcusparse.so*" -exec ln -sf {} /usr/local/cuda/lib64/ \; 2>/dev/null || true

# 设置 CUDA 环境变量
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# 验证 nvcc
RUN nvcc --version && \
    test -f /usr/local/cuda/bin/nvcc && echo "CUDA symlink created successfully"

# 复制requirements.txt到/workspace
COPY requirements.txt /workspace/requirements.txt
RUN pip install -r /workspace/requirements.txt

CMD ["/bin/bash"]
