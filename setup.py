import os
import sys
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

# Version
VERSION = '1.21.0'

class OptimizedBuildExt(build_ext):
    """Custom build extension to add optimization flags"""
    def build_extensions(self):
        # Optimization flags
        extra_compile_args = [
            '-O3',  # Maximum optimization
            '-ffast-math',  # Fast floating point
            '-funroll-loops',  # Loop unrolling
            '-fomit-frame-pointer',  # Omit frame pointer
        ]
        
        # Add architecture-specific optimizations
        import platform
        if platform.machine() == 'arm64' and sys.platform == 'darwin':
            # Apple Silicon
            extra_compile_args.append('-mcpu=apple-m1')
        elif platform.machine() in ('x86_64', 'amd64'):
            # Intel/AMD
            extra_compile_args.extend(['-march=native', '-mtune=native'])
            
        # Link time optimization (not always supported)
        if sys.platform != 'darwin':
            extra_compile_args.append('-flto')
            extra_link_args = ['-flto']
        else:
            extra_link_args = []
        
        # Platform-specific flags
        if sys.platform == 'darwin':
            extra_compile_args.extend([
                '-Wno-unused-command-line-argument',
                '-mmacosx-version-min=10.9',
            ])
        elif sys.platform.startswith('linux'):
            extra_compile_args.extend([
                '-pthread',
                '-D_GNU_SOURCE',
            ])
        
        # Add optimization flags to all extensions
        for ext in self.extensions:
            ext.extra_compile_args = getattr(ext, 'extra_compile_args', []) + extra_compile_args
            ext.extra_link_args = getattr(ext, 'extra_link_args', []) + extra_link_args
        
        super().build_extensions()

# Define macros based on platform
define_macros = [
    ('WEBFS_VERSION', f'"{VERSION}"'),
    ('_LARGEFILE_SOURCE', None),
    ('_LARGEFILE64_SOURCE', None),
    ('_FILE_OFFSET_BITS', '64'),
]

# Platform-specific settings
libraries = []
extra_link_args = []

if sys.platform == 'darwin':
    define_macros.append(('MIMEFILE', '"/usr/share/cups/mime/mime.types"'))
    libraries.extend(['pthread'])
else:
    define_macros.append(('MIMEFILE', '"/etc/mime.types"'))
    libraries.extend(['pthread'])
    if sys.platform.startswith('linux'):
        extra_link_args.append('-Wl,-O1')  # Optimize linker

# Check for SSL support
try:
    import subprocess
    result = subprocess.run(['pkg-config', '--exists', 'openssl'], capture_output=True)
    if result.returncode == 0:
        define_macros.append(('USE_SSL', '1'))
        libraries.extend(['ssl', 'crypto'])
except:
    pass

# C extension module - simple wrapper that calls webfsd binary
webfsd_module = Extension(
    'fasthttp._webfsd',
    sources=['webfsd_python.c'],
    define_macros=[],
    extra_compile_args=['-O3'],
    language='c',
)

# Filter out None sources
webfsd_module.sources = [s for s in webfsd_module.sources if s is not None]

# Long description
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='fasthttp',
    version=VERSION,
    author='Gerd Knorr (original), Python wrapper contributors',
    author_email='',
    description='Ultra-fast lightweight HTTP server',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/fasthttp',
    packages=['fasthttp'],
    ext_modules=[webfsd_module],
    cmdclass={
        'build_ext': OptimizedBuildExt,
    },
    package_data={
        'fasthttp': ['../webfsd'],
    },
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: C',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'fasthttp=fasthttp.__main__:main',
        ],
    },
    zip_safe=False,
)