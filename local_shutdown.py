#!/usr/bin/env python3
"""Simple shutdown script"""

import os
import signal
import subprocess
import sys

def find_process_by_port(port=8000):
    """Find process running on the specified port"""
    try:
        if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip())
        elif sys.platform.startswith('win'):
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        return int(parts[-1])
    except Exception:
        pass
    return None

def main():
    port = 8000
    pid = find_process_by_port(port)
    
    if not pid:
        print(f"No process found running on port {port}")
        return
    
    print(f"Stopping application (PID: {pid})...")
    try:
        os.kill(pid, signal.SIGTERM)
        print("Application stopped successfully")
    except ProcessLookupError:
        print("Process not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
