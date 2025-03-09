#!/usr/bin/env python3
"""
ExtractorPlus Plugin Docker Build Script
---------------------------------------
This script uses Docker to build egg files for multiple Python versions.
It doesn't require any Python versions to be installed locally other than
the one running this script.

Usage: python build_docker.py

Requirements:
- Python 3.6+
- Docker installed and running

Author: ExtractorPlus Team
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Version range to build for
PYTHON_VERSIONS = ["3.6", "3.7", "3.8", "3.9", "3.10", "3.11", "3.12"]

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'

def print_status(message, status, color=GREEN):
    """Print a status message with color."""
    print(f"{message.ljust(50)} [{color}{status}{ENDC}]")

def check_docker():
    """Check if Docker is installed and running."""
    try:
        subprocess.run(
            ["docker", "--version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def build_egg_with_docker(version):
    """Build an egg file using Docker with the specified Python version."""
    try:
        # Get the absolute path to the current directory
        project_dir = os.path.abspath(os.getcwd())
        dist_dir = os.path.join(project_dir, "dist")
        
        # Make sure dist directory exists
        os.makedirs(dist_dir, exist_ok=True)
        
        # Create a Dockerfile in a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dockerfile") as temp:
            temp_path = temp.name
            docker_content = f"""FROM python:{version}-slim
WORKDIR /app
COPY . /app
RUN pip install setuptools
RUN python setup.py bdist_egg
"""
            temp.write(docker_content.encode())
        
        # Create a unique container name
        container_name = f"extractorplus-build-py{version.replace('.', '')}"
        
        print(f"Building for Python {version} using Docker...", end="", flush=True)
        
        # Build the Docker image
        build_command = [
            "docker", "build", 
            "-f", temp_path,
            "-t", container_name,
            "."
        ]
        
        subprocess.run(
            build_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        # Create and run the container to extract the egg file
        run_command = [
            "docker", "run",
            "--name", container_name,
            container_name
        ]
        
        subprocess.run(
            run_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        # Copy the egg file from the container to the dist directory
        cp_command = [
            "docker", "cp",
            f"{container_name}:/app/dist/.", 
            dist_dir
        ]
        
        subprocess.run(
            cp_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        # Clean up
        subprocess.run(
            ["docker", "rm", container_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        subprocess.run(
            ["docker", "rmi", container_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Delete the temporary Dockerfile
        os.unlink(temp_path)
        
        # Find the egg file that was just created
        egg_files = list(Path(dist_dir).glob(f"*-py{version.replace('.', '')}.egg"))
        
        if egg_files:
            egg_path = egg_files[0]
            egg_size = egg_path.stat().st_size / 1024  # KB
            print(f"\r", end="", flush=True)
            print_status(f"Python {version}", f"SUCCESS - {egg_path.name} ({egg_size:.1f} KB)")
            return True
        else:
            print(f"\r", end="", flush=True)
            print_status(f"Python {version}", "SUCCESS - But egg file not found", YELLOW)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\r", end="", flush=True)
        print_status(f"Python {version}", "FAILED", RED)
        if e.stderr:
            print(f"  Error: {e.stderr.decode().strip()}")
        return False

def main():
    """Main function."""
    print(f"{BOLD}ExtractorPlus Docker Build Script{ENDC}")
    print("================================")
    
    # Check if Docker is installed and running
    if not check_docker():
        print(f"{RED}Docker is not installed or not running.{ENDC}")
        print("Please install Docker and make sure it's running.")
        return 1
    
    print(f"Building eggs for Python versions: {', '.join(PYTHON_VERSIONS)}")
    
    # Create dist directory if it doesn't exist
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    
    # Build for each Python version
    success_count = 0
    for version in PYTHON_VERSIONS:
        if build_egg_with_docker(version):
            success_count += 1
    
    # Print summary
    print("\nBuild Summary")
    print("============")
    print(f"Total Python versions attempted: {len(PYTHON_VERSIONS)}")
    print(f"Successfully built eggs: {success_count}")
    
    print(f"\nEgg files are located in the '{dist_dir}' directory")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 