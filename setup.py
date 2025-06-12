import os
import shutil
import subprocess
import sys

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext
from setuptools.command.build_py import build_py
from setuptools.command.install import install

# Version
VERSION = "1.21.5"


class BuildWebfsd(build_py):
    """Custom build command to compile httpit binary"""

    def run(self):
        # Build webfsd binary if not already built
        if not os.path.exists("webfsd") and os.path.exists("webfsd.c"):
            print("Building webfsd binary...")
            try:
                # Clean first
                subprocess.run(["make", "clean"], capture_output=True)
                # Build webfsd
                result = subprocess.run(
                    ["make", "webfsd"], capture_output=True, text=True
                )
                if result.returncode != 0:
                    print("Warning: Could not build webfsd binary")
                    print(result.stdout)
                    print(result.stderr)
                else:
                    print("webfsd binary built successfully")
            except Exception as e:
                print(f"Warning: Could not build webfsd binary: {e}")

        # Continue with normal build
        super().run()

        # Copy webfsd binary to package if it exists
        if os.path.exists("webfsd"):
            # Ensure package directory exists
            package_dir = os.path.join(self.build_lib, "fasthttp")
            os.makedirs(package_dir, exist_ok=True)

            # Copy binary
            dest = os.path.join(package_dir, "webfsd")
            shutil.copy2("webfsd", dest)
            os.chmod(dest, 0o755)
            print(f"Copied webfsd binary to {dest}")


class OptimizedBuildExt(build_ext):
    """Custom build extension to add optimization flags"""

    def build_extensions(self):
        import platform

        # Check if we're in CI/CD environment
        is_ci = os.environ.get("CI", "false").lower() == "true"
        is_cibuildwheel = os.environ.get("CIBUILDWHEEL", "0") == "1"
        optimize = os.environ.get("FASTHTTP_OPTIMIZE", "1") == "1"

        extra_compile_args = []
        extra_link_args = []

        if sys.platform == "win32":
            # Windows (MSVC)
            if optimize:
                extra_compile_args.extend(["/O2", "/GL"])
                extra_link_args.extend(["/LTCG"])
        else:
            # Unix-like systems (GCC/Clang)
            if optimize:
                extra_compile_args.extend(
                    [
                        "-O3",  # Maximum optimization
                        "-ffast-math",  # Fast floating point
                        "-funroll-loops",  # Loop unrolling
                        "-fomit-frame-pointer",  # Omit frame pointer
                    ]
                )

            # Architecture-specific optimizations only when not building wheels
            if not (is_ci or is_cibuildwheel):
                if platform.machine() == "arm64" and sys.platform == "darwin":
                    # Apple Silicon
                    extra_compile_args.append("-mcpu=apple-m1")
                elif platform.machine() in ("x86_64", "amd64"):
                    # Intel/AMD - use native only when not building distributable wheels
                    extra_compile_args.extend(["-march=native", "-mtune=native"])

            # Platform-specific flags
            if sys.platform == "darwin":
                extra_compile_args.extend(
                    [
                        "-Wno-unused-command-line-argument",
                        "-mmacosx-version-min=10.9",
                    ]
                )
            elif sys.platform.startswith("linux"):
                extra_compile_args.extend(
                    [
                        "-pthread",
                        "-D_GNU_SOURCE",
                    ]
                )

        # Add optimization flags to all extensions
        for ext in self.extensions:
            ext.extra_compile_args = (
                getattr(ext, "extra_compile_args", []) + extra_compile_args
            )
            ext.extra_link_args = getattr(ext, "extra_link_args", []) + extra_link_args

        super().build_extensions()


# Define macros based on platform
define_macros = [
    ("WEBFS_VERSION", f'"{VERSION}"'),
    ("_LARGEFILE_SOURCE", None),
    ("_LARGEFILE64_SOURCE", None),
    ("_FILE_OFFSET_BITS", "64"),
]

# Platform-specific settings
libraries = []
extra_link_args = []

if sys.platform == "darwin":
    define_macros.append(("MIMEFILE", '"/usr/share/cups/mime/mime.types"'))
    libraries.extend(["pthread"])
else:
    define_macros.append(("MIMEFILE", '"/etc/mime.types"'))
    libraries.extend(["pthread"])
    if sys.platform.startswith("linux"):
        extra_link_args.append("-Wl,-O1")  # Optimize linker

# Check for SSL support
try:
    import subprocess

    result = subprocess.run(["pkg-config", "--exists", "openssl"], capture_output=True)
    if result.returncode == 0:
        define_macros.append(("USE_SSL", "1"))
        libraries.extend(["ssl", "crypto"])
except:
    pass

# C extension module - simple wrapper that calls webfsd binary
webfsd_module = Extension(
    "fasthttp._webfsd",
    sources=["webfsd_python.c"],
    define_macros=[],
    extra_compile_args=["-O3"],
    language="c",
)

# Filter out None sources
webfsd_module.sources = [s for s in webfsd_module.sources if s is not None]

# Long description
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="fasthttp",
    version=VERSION,
    author="Farshid Ashouri",
    author_email="",
    description="Ultra-fast lightweight HTTP server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/httpit",
    packages=["fasthttp"],
    ext_modules=[webfsd_module],
    cmdclass={
        "build_ext": OptimizedBuildExt,
        "build_py": BuildWebfsd,
    },
    package_data={
        "fasthttp": ["../webfsd"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: C",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "fasthttp=fasthttp.__main__:main",
        ],
    },
    zip_safe=False,
)
