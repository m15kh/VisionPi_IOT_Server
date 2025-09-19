import torch, time

print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU name:", torch.cuda.get_device_name(0))
    # یک عملیات ساده روی GPU
    a = torch.randn(10000, 10000, device="cuda")
    b = torch.randn(10000, 10000, device="cuda")
    torch.cuda.synchronize()
    t0 = time.time()
    c = a @ b
    torch.cuda.synchronize()
    print("Matmul time (s):", time.time() - t0)
else:
    print("No CUDA device detected by PyTorch")
