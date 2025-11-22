#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print("BOT GPT Backend - Local Start")
    print("=" * 60)
    print()
    
    project_root = Path(__file__).parent.resolve()
    venv_dir = project_root / "venv"
    data_dir = project_root / "data"
    
    if not venv_dir.exists():
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        print("✅ Virtual environment created")
        print()
    else:
        print("✅ Virtual environment exists")
        print()
    
    if os.name == 'nt':
        venv_python = venv_dir / "Scripts" / "python.exe"
        pip_cmd = venv_dir / "Scripts" / "pip.exe"
    else:
        venv_python = venv_dir / "bin" / "python"
        pip_cmd = venv_dir / "bin" / "pip"
    
    print("📦 Upgrading pip...")
    try:
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        print("✅ pip upgraded")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Could not upgrade pip: {e}")
    print()
    
    print("📦 Installing dependencies from requirements.txt...")
    print("    (This may take a minute on first run...)")
    print()
    try:
        result = subprocess.run([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"], 
                              check=True)
        print()
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("   Please run manually: pip install -r requirements.txt")
        sys.exit(1)
    print()
    
    if not data_dir.exists():
        print("📁 Creating data directory...")
        data_dir.mkdir(parents=True, exist_ok=True)
        print("✅ Data directory created")
    else:
        print("✅ Data directory exists")
    print()
    
    env_file = project_root / ".env"
    if env_file.exists():
        print("✅ .env file exists")
    else:
        print("💡 No .env file (using defaults: port 8000, mock LLM, SQLite)")
        print("   To customize: copy .env.example to .env and edit")
    print()
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    
    print("=" * 60)
    print("🚀 Starting BOT GPT Backend...")
    print("=" * 60)
    print()
    print("📡 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/api/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print()
    print("Press CTRL+C to stop")
    print()
    
    try:
        subprocess.run([
            str(venv_python),
            "-m",
            "uvicorn",
            "src.main.python.test_python_app.app:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], env=env, check=True)
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("🛑 Application stopped")
        print("=" * 60)
    except subprocess.CalledProcessError as e:
        print()
        print(f"❌ Error starting application: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check if port 8000 is already in use")
        print("  2. Try: python -m uvicorn test_python_app.app:app --reload")
        print("  3. Check logs above for detailed error")
        sys.exit(1)

if __name__ == "__main__":
    main()
