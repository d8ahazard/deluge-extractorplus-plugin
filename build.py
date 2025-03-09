#!/usr/bin/env python3
"""
ExtractorPlus Plugin Build Script
--------------------------------
This script builds egg files for multiple Python versions.
It detects installed Python versions and builds an egg for each.

Usage: python build.py

Requirements:
- Python 3.6+
- setuptools

Author: ExtractorPlus Team
"""

import os
import platform
import subprocess
import sys
from pathlib import Path
import shutil

# Version range to build for
MIN_VERSION = 6  # 3.6
MAX_VERSION = 12  # 3.12

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'

def print_status(message, status, color=GREEN):
    """Print a status message with color."""
    print(f"{message.ljust(50)} [{color}{status}{ENDC}]")

def find_python_installations():
    """Find Python installations on the system."""
    python_exes = []
    system = platform.system()
    
    if system == "Windows":
        # Check common Windows install locations
        base_paths = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Python'),
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Python'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Python')
        ]
        
        # Look for Python executables in standard Windows locations
        for base_path in base_paths:
            if os.path.exists(base_path):
                for version in range(MIN_VERSION, MAX_VERSION + 1):
                    version_str = f"3{version}"
                    python_path = os.path.join(base_path, f"Python{version_str}", "python.exe")
                    if os.path.exists(python_path):
                        python_exes.append((python_path, f"3.{version}"))
    else:
        # For Linux/macOS, check for python3.X in PATH
        for version in range(MIN_VERSION, MAX_VERSION + 1):
            # Try which python3.X
            try:
                python_path = subprocess.check_output(
                    ["which", f"python3.{version}"], 
                    stderr=subprocess.DEVNULL, 
                    universal_newlines=True
                ).strip()
                if python_path:
                    python_exes.append((python_path, f"3.{version}"))
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Also try looking in common locations like /usr/bin
                common_paths = ["/usr/bin", "/usr/local/bin", "/opt/homebrew/bin"]
                for path in common_paths:
                    python_path = os.path.join(path, f"python3.{version}")
                    if os.path.exists(python_path) and os.access(python_path, os.X_OK):
                        python_exes.append((python_path, f"3.{version}"))
                        break
    
    return python_exes

def build_egg(python_exe, version):
    """Build an egg file using the specified Python executable."""
    try:
        print(f"Building for Python {version} using {python_exe}...", end="", flush=True)
        result = subprocess.run(
            [python_exe, "setup.py", "bdist_egg"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True
        )
        print(f"\r", end="", flush=True)
        
        # Find the egg file that was just created
        dist_path = Path("dist")
        egg_files = list(dist_path.glob(f"*-py{version.replace('.', '')}.egg"))
        
        if egg_files:
            egg_path = egg_files[0]
            egg_size = egg_path.stat().st_size / 1024  # KB
            print_status(f"Python {version}", f"SUCCESS - {egg_path.name} ({egg_size:.1f} KB)")
            return True
        else:
            print_status(f"Python {version}", "SUCCESS - But egg file not found", YELLOW)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\r", end="", flush=True)
        print_status(f"Python {version}", "FAILED", RED)
        print(f"  Error: {e.stderr.strip()}")
        return False

def main():
    """Main function."""
    print(f"{BOLD}ExtractorPlus Plugin Build Script{ENDC}")
    print("============================")
    
    # Create dist directory if it doesn't exist
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    
    # Find Python installations
    python_installations = find_python_installations()
    
    if not python_installations:
        print(f"{RED}No Python installations found for versions 3.{MIN_VERSION}-3.{MAX_VERSION}{ENDC}")
        print("Please install Python versions you want to build for.")
        return 1
    
    print(f"Found {len(python_installations)} Python installations")
    
    # Build for each Python version
    success_count = 0
    for python_exe, version in python_installations:
        if build_egg(python_exe, version):
            success_count += 1
    
    # Print summary
    print("\nBuild Summary")
    print("============")
    print(f"Total Python versions found: {len(python_installations)}")
    print(f"Successfully built eggs: {success_count}")
    
    print(f"\nEgg files are located in the '{dist_dir}' directory")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 