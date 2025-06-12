"""
Embedded httpit binary management
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path


def get_webfsd_path():
    """Get the path to the webfsd binary."""
    # Try different locations
    locations = [
        # Development location
        Path(__file__).parent.parent / 'webfsd',
        # Installed location (same directory as this file)
        Path(__file__).parent / 'webfsd',
        # System locations
        Path('/usr/local/bin/webfsd'),
        Path('/usr/bin/webfsd'),
    ]
    
    for path in locations:
        if path.exists() and os.access(str(path), os.X_OK):
            return str(path)
    
    # Try to find in PATH
    webfsd_in_path = shutil.which('webfsd')
    if webfsd_in_path:
        return webfsd_in_path
    
    # Extract embedded binary if available
    try:
        import pkg_resources
        binary_data = pkg_resources.resource_string('fasthttp', 'webfsd')
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(prefix='webfsd_', delete=False) as f:
            f.write(binary_data)
            temp_path = f.name
        
        # Make executable
        os.chmod(temp_path, 0o755)
        
        return temp_path
    except:
        pass
    
    raise RuntimeError("Could not find httpit binary. Please ensure it is built and available.")