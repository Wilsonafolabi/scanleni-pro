import sys

packages = {
    "paddleocr": "paddleocr",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "pydantic": "pydantic",
    "PIL": "pillow",
    "numpy": "numpy",
    "requests": "requests"
}

print("🔍 Verifying core packages...")
all_ok = True
for import_name, pip_name in packages.items():
    try:
        __import__(import_name)
        print(f"✅ {pip_name}")
    except ImportError as e:
        print(f"❌ {pip_name} - {e}")
        all_ok = False

if all_ok:
    print("\n🎉 Environment ready. Proceed to Phase 1.")
else:
    print("\n⚠️ Some packages failed. Run: pip install <missing_package>")
sys.exit(0 if all_ok else 1)