import torch

# 查看 PyTorch 版本
print(f"PyTorch version: {torch.__version__}")

# 查看 CUDA 是否可用
is_cuda_available = torch.cuda.is_available()
print(f"CUDA Available: {is_cuda_available}")

# 如果 CUDA 可用，查看 CUDA 版本和 GPU 设备信息
if is_cuda_available:
    print(f"CUDA Version: {torch.version.cuda}")
    print(f"Device Name: {torch.cuda.get_device_name(0)}")
    print(f"Number of CUDA devices: {torch.cuda.device_count()}")
