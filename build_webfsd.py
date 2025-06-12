#!/usr/bin/env python3
"""
Build script for webfsd binary.
This is called during the wheel building process to compile webfsd.
"""

import os
import sys
import subprocess
import shutil
import platform

def build_webfsd():
    """Build the webfsd binary for the current platform."""
    print("Building webfsd binary...")
    
    # Clean any existing build
    if os.path.exists('webfsd'):
        os.remove('webfsd')
    
    # Run make clean
    subprocess.run(['make', 'clean'], capture_output=True)
    
    # Build webfsd
    env = os.environ.copy()
    
    # Set optimization flags
    if platform.system() == 'Darwin':
        env['CFLAGS'] = '-O3 -ffast-math -funroll-loops -fomit-frame-pointer'
    elif platform.system() == 'Linux':
        env['CFLAGS'] = '-O3 -ffast-math -funroll-loops -fomit-frame-pointer -fPIC'
    elif platform.system() == 'Windows':
        # For Windows, we might need a different build approach
        print("Windows build not yet implemented")
        return False
    
    # Run make
    result = subprocess.run(['make', 'webfsd'], env=env, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Build failed:")
        print(result.stdout)
        print(result.stderr)
        return False
    
    # Check if binary was created
    if not os.path.exists('webfsd'):
        print("webfsd binary not found after build")
        return False
    
    # Make it executable
    os.chmod('webfsd', 0o755)
    
    # Copy to fasthttp package directory
    package_dir = os.path.join(os.path.dirname(__file__), 'fasthttp')
    if not os.path.exists(package_dir):
        os.makedirs(package_dir)
    
    shutil.copy2('webfsd', package_dir)
    print(f"webfsd binary built and copied to {package_dir}")
    
    return True

if __name__ == '__main__':
    if not build_webfsd():
        sys.exit(1)
    print("Build successful!")