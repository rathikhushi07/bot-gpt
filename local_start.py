#!/usr/bin/env python3
"""Simple start script for local development"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    project_root = Path(__file__).parent.resolve()
    venv_dir = project_root / "venv"
    
    # Create venv if it doesn't exist
    if not venv_dir.exists():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        print("Virtual environment created")
    
    # Determine Python path
    if os.name == 'nt':
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"
    
    # Install dependencies if needed
    try:
        subprocess.run([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pass  # Dependencies might already be installed
    
    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    
    print(f"Starting application on http://localhost:8000")
    print("Press CTRL+C to stop\n")
    
    # Start the app
    try:
        subprocess.run([
            str(venv_python),
            "-m",
            "uvicorn",
            "src.main.python.test_python_app.app:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], env=env)
    except KeyboardInterrupt:
        print("\nApplication stopped")

if __name__ == "__main__":
    main()
