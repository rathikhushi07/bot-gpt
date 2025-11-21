#!/usr/bin/env python3
"""
Run tests with proper PYTHONPATH
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get project root
    project_root = Path(__file__).parent.resolve()
    
    # Set PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    
    print("=" * 50)
    print("Running tests for test-python-app")
    print("=" * 50)
    print(f"Project root: {project_root}")
    print(f"PYTHONPATH: {env['PYTHONPATH']}")
    print("=" * 50)
    
    # Run pytest
    subprocess.run([
        sys.executable,
        "-m",
        "pytest",
        "src/test/python/",
        "-v",
        "--cov=src/main/python",
        "--cov-report=html",
        "--cov-report=term-missing"
    ], env=env)

if __name__ == "__main__":
    main()







