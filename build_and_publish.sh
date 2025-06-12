#!/bin/bash
# Build and publish httpit package for Python 3.9 to 3.13
# Copyright (c) RODMENA LIMITED
# https://rodmena.co.uk

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PACKAGE_NAME="httpit"
PYTHON_VERSIONS=("3.9" "3.10" "3.11" "3.12" "3.13")
VENV_BASE_DIR="build_venvs"
DOCKER_PLATFORMS=("linux/amd64" "linux/arm64")
USE_DOCKER=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Function to check if Python version is installed
check_python_version() {
    local version=$1
    if command -v python$version &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to check if Docker is available and configured
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        return 1
    fi
    
    # Check if buildx is available for multi-platform builds
    if ! docker buildx version &> /dev/null; then
        print_error "Docker buildx is not available"
        return 1
    fi
    
    return 0
}

# Function to create Dockerfile for building wheels
create_dockerfile() {
    cat > Dockerfile.build << 'EOF'
# Multi-stage Dockerfile for building Python wheels
ARG PYTHON_VERSION=3.9

FROM python:${PYTHON_VERSION}-slim-bullseye

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy source code
COPY . .

# Install Python build tools
RUN pip install --upgrade pip setuptools wheel build

# Build the package
RUN python -m build --wheel --outdir /wheels/

# List built wheels
RUN ls -la /wheels/
EOF
    print_success "Created Dockerfile for building wheels"
}

# Function to build wheels using Docker
build_wheels_docker() {
    print_status "Building wheels using Docker for multiple platforms..."
    
    if ! check_docker; then
        print_error "Docker is not available, falling back to local builds"
        return 1
    fi
    
    # Create Dockerfile
    create_dockerfile
    
    # Create builder instance for multi-platform builds
    docker buildx create --name httpit-builder --use --bootstrap >/dev/null 2>&1 || true
    
    local total_built=0
    
    # Build for each Python version and platform
    for py_version in "${PYTHON_VERSIONS[@]}"; do
        for platform in "${DOCKER_PLATFORMS[@]}"; do
            print_status "Building wheel for Python ${py_version} on ${platform}..."
            
            # Build the wheel for this platform and Python version
            if docker buildx build \
                --platform ${platform} \
                --build-arg PYTHON_VERSION=${py_version} \
                --output type=local,dest=./docker_wheels/${platform//\//_}/py${py_version} \
                -f Dockerfile.build \
                . >/dev/null 2>&1; then
                
                print_success "Built wheel for Python ${py_version} on ${platform}"
                ((total_built++))
            else
                print_warning "Failed to build wheel for Python ${py_version} on ${platform}"
            fi
        done
    done
    
    # Collect all wheels into dist/ directory
    if [ -d "docker_wheels" ]; then
        mkdir -p dist/
        find docker_wheels/ -name "*.whl" -exec cp {} dist/ \; 2>/dev/null || true
        
        # Remove docker build artifacts
        rm -rf docker_wheels/
    fi
    
    # Clean up Dockerfile
    rm -f Dockerfile.build
    
    # Remove builder instance
    docker buildx rm httpit-builder >/dev/null 2>&1 || true
    
    if [ $total_built -gt 0 ]; then
        print_success "Built $total_built wheels using Docker"
        return 0
    else
        print_error "No wheels were built using Docker"
        return 1
    fi
}

# Function to build wheels using cibuildwheel (alternative approach)
build_wheels_cibuildwheel() {
    print_status "Building wheels using cibuildwheel..."
    
    # Create a temporary venv for cibuildwheel
    python3 -m venv ${VENV_BASE_DIR}/venv_cibw
    source ${VENV_BASE_DIR}/venv_cibw/bin/activate
    
    pip install --upgrade pip cibuildwheel >/dev/null 2>&1
    
    # Set environment variables for cibuildwheel
    export CIBW_BUILD="cp39-* cp310-* cp311-* cp312-* cp313-*"
    export CIBW_SKIP="*-win32 *-manylinux_i686 pp*"
    export CIBW_ARCHS_LINUX="x86_64 aarch64"
    export CIBW_ARCHS_MACOS="x86_64 arm64 universal2"
    
    # Build wheels
    if cibuildwheel --output-dir dist/; then
        print_success "Built wheels using cibuildwheel"
        deactivate
        return 0
    else
        print_error "Failed to build wheels using cibuildwheel"
        deactivate
        return 1
    fi
}

# Function to clean up
cleanup() {
    print_status "Cleaning up build artifacts..."
    
    # Remove build directories
    rm -rf build/ dist/ *.egg-info/ ${PACKAGE_NAME}.egg-info/
    rm -rf .eggs/ .pytest_cache/ htmlcov/
    rm -rf ${VENV_BASE_DIR}/
    
    # Remove compiled files
    find . -type f -name '*.pyc' -delete
    find . -type f -name '*.pyo' -delete
    find . -type f -name '*.so' -delete
    find . -type f -name '*.o' -delete
    find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
    
    # Clean C build artifacts
    make clean >/dev/null 2>&1 || true
    
    print_success "Cleanup completed"
}

# Function to build C extension
build_c_extension() {
    print_status "Building C extension (webfsd)..."
    
    if ! make; then
        print_error "Failed to build C extension"
        exit 1
    fi
    
    if [ ! -f "webfsd" ]; then
        print_error "webfsd binary not found after build"
        exit 1
    fi
    
    print_success "C extension built successfully"
}

# Function to create virtual environment and build wheel
build_for_python() {
    local python_version=$1
    local venv_dir="${VENV_BASE_DIR}/venv_py${python_version}"
    
    print_status "Building for Python ${python_version}..."
    
    # Check if Python version is available
    if ! check_python_version $python_version; then
        print_warning "Python ${python_version} not found, skipping..."
        return 1
    fi
    
    # Create virtual environment
    print_status "Creating virtual environment for Python ${python_version}..."
    python${python_version} -m venv ${venv_dir}
    
    # Activate virtual environment
    source ${venv_dir}/bin/activate
    
    # Upgrade pip and install build tools
    print_status "Installing build tools..."
    pip install --upgrade pip setuptools wheel build twine >/dev/null 2>&1
    
    # Build the package
    print_status "Building package..."
    python -m build --wheel --outdir dist/
    
    # Deactivate virtual environment
    deactivate
    
    print_success "Built wheel for Python ${python_version}"
    return 0
}

# Function to build source distribution
build_sdist() {
    print_status "Building source distribution..."
    
    # Create a temporary venv for building sdist
    python3 -m venv ${VENV_BASE_DIR}/venv_sdist
    source ${VENV_BASE_DIR}/venv_sdist/bin/activate
    
    pip install --upgrade pip build >/dev/null 2>&1
    python -m build --sdist --outdir dist/
    
    deactivate
    
    print_success "Source distribution built"
}

# Function to check package integrity
check_packages() {
    print_status "Checking package integrity..."
    
    # Create a test venv
    python3 -m venv ${VENV_BASE_DIR}/venv_test
    source ${VENV_BASE_DIR}/venv_test/bin/activate
    
    pip install --upgrade twine >/dev/null 2>&1
    
    # Check all distributions
    if twine check dist/*; then
        print_success "All packages passed integrity checks"
    else
        print_error "Package integrity check failed"
        deactivate
        return 1
    fi
    
    deactivate
    return 0
}

# Function to publish to PyPI
publish_to_pypi() {
    local repository=$1  # 'pypi' or 'testpypi'
    
    print_status "Publishing to ${repository}..."
    
    # Create a venv for publishing
    python3 -m venv ${VENV_BASE_DIR}/venv_publish
    source ${VENV_BASE_DIR}/venv_publish/bin/activate
    
    pip install --upgrade twine >/dev/null 2>&1
    
    # Set repository URL
    local repo_args=""
    if [ "$repository" = "testpypi" ]; then
        repo_args="--repository testpypi"
    fi
    
    # Upload packages
    if [ -n "$TWINE_USERNAME" ] && [ -n "$TWINE_PASSWORD" ]; then
        # Use environment variables if set
        twine upload ${repo_args} dist/*
    else
        # Interactive mode
        print_warning "No TWINE_USERNAME/TWINE_PASSWORD found, using interactive mode"
        print_warning "Username should be: __token__"
        print_warning "Password should be your PyPI API token (starts with pypi-)"
        twine upload ${repo_args} dist/*
    fi
    
    deactivate
}

# Main script
main() {
    echo "=========================================="
    echo "   ${PACKAGE_NAME} Build & Publish Script"
    echo "   Copyright (c) RODMENA LIMITED"
    echo "   https://rodmena.co.uk"
    echo "=========================================="
    echo ""
    
    # Parse command line arguments
    SKIP_CLEANUP=false
    SKIP_BUILD=false
    SKIP_PUBLISH=false
    TEST_PYPI=false
    USE_CIBUILDWHEEL=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-cleanup)
                SKIP_CLEANUP=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-publish)
                SKIP_PUBLISH=true
                shift
                ;;
            --test-pypi)
                TEST_PYPI=true
                shift
                ;;
            --docker)
                USE_DOCKER=true
                shift
                ;;
            --cibuildwheel)
                USE_CIBUILDWHEEL=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --skip-cleanup    Skip cleanup step"
                echo "  --skip-build      Skip build step"
                echo "  --skip-publish    Skip publish step"
                echo "  --test-pypi       Publish to TestPyPI instead of PyPI"
                echo "  --docker          Use Docker for cross-platform wheel building"
                echo "  --cibuildwheel    Use cibuildwheel for wheel building"
                echo "  --help, -h        Show this help message"
                echo ""
                echo "Build methods:"
                echo "  Default:          Local venvs for available Python versions"
                echo "  --docker:         Docker multi-platform builds (requires Docker)"
                echo "  --cibuildwheel:   Professional wheel building (recommended for CI)"
                echo ""
                echo "Environment variables:"
                echo "  TWINE_USERNAME    PyPI username (use '__token__' for token auth)"
                echo "  TWINE_PASSWORD    PyPI password or API token"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Step 1: Cleanup
    if [ "$SKIP_CLEANUP" = false ]; then
        cleanup
    fi
    
    # Step 2: Build
    if [ "$SKIP_BUILD" = false ]; then
        # Create build directory
        mkdir -p ${VENV_BASE_DIR}
        
        # Build C extension
        build_c_extension
        
        # Build source distribution
        build_sdist
        
        # Choose build method
        built_count=0
        
        if [ "$USE_CIBUILDWHEEL" = true ]; then
            # Use cibuildwheel for professional wheel building
            if build_wheels_cibuildwheel; then
                built_count=$(ls dist/*.whl 2>/dev/null | wc -l || echo 0)
            fi
        elif [ "$USE_DOCKER" = true ]; then
            # Use Docker for cross-platform builds
            if build_wheels_docker; then
                built_count=$(ls dist/*.whl 2>/dev/null | wc -l || echo 0)
            fi
        else
            # Use local Python installations
            for py_version in "${PYTHON_VERSIONS[@]}"; do
                if build_for_python $py_version; then
                    ((built_count++))
                fi
            done
        fi
        
        if [ $built_count -eq 0 ]; then
            print_error "No wheels were built. Please install Python versions or use --docker/--cibuildwheel."
            exit 1
        fi
        
        print_success "Built $built_count wheels total"
        
        # Check all packages
        if ! check_packages; then
            exit 1
        fi
        
        # List built packages
        echo ""
        print_status "Built packages:"
        ls -la dist/
        echo ""
    fi
    
    # Step 3: Publish
    if [ "$SKIP_PUBLISH" = false ]; then
        if [ "$TEST_PYPI" = true ]; then
            publish_to_pypi "testpypi"
            echo ""
            print_success "Published to TestPyPI!"
            print_status "Install from TestPyPI with:"
            echo "  pip install --index-url https://test.pypi.org/simple/ ${PACKAGE_NAME}"
        else
            publish_to_pypi "pypi"
            echo ""
            print_success "Published to PyPI!"
            print_status "Install from PyPI with:"
            echo "  pip install ${PACKAGE_NAME}"
        fi
    fi
    
    # Final cleanup of venvs
    if [ -d "${VENV_BASE_DIR}" ]; then
        print_status "Cleaning up virtual environments..."
        rm -rf ${VENV_BASE_DIR}
    fi
    
    echo ""
    print_success "All done!"
}

# Run main function
main "$@"