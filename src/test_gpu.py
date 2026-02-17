import torch

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"Device: {torch.cuda.get_device_name(0)}")
    print(f"Capability: {torch.cuda.get_device_capability()}")

    # Test GPU tensor
    x = torch.tensor([1.0, 2.0, 3.0], device="cuda")
    y = x * 2
    print(f"GPU tensor test: {y}")
    print("PyTorch GPU works!")
else:
    print("No GPU available")