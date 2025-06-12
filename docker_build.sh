#!/bin/bash
# Docker-based cross-platform wheel builder for httpit
# Copyright (c) RODMENA LIMITED
# https://rodmena.co.uk

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[*]${NC} $1"; }
print_success() { echo -e "${GREEN}[✓]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }

# Configuration
PYTHON_VERSIONS=("3.9" "3.10" "3.11" "3.12" "3.13")
PLATFORMS=("linux/amd64" "linux/arm64")

# Create multi-stage Dockerfile
create_dockerfile() {
    cat > Dockerfile.multiarch << 'EOF'
# Multi-platform Dockerfile for building httpit wheels
ARG PYTHON_VERSION=3.11
ARG TARGETPLATFORM

# Use appropriate base image based on platform
FROM --platform=$TARGETPLATFORM python:${PYTHON_VERSION}-slim-bookworm

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libc6-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy source code
COPY . .

# Install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel build

# Build the webfsd C extension first
RUN make clean && make

# Build the Python wheel
RUN python -m build --wheel --outdir /dist/

# List the built wheel with platform info
RUN echo "Built wheel:" && ls -la /dist/ && \
    echo "Platform: $TARGETPLATFORM" && \
    echo "Architecture: $(uname -m)" && \
    python -c "import platform; print(f'Python: {platform.python_version()}, Machine: {platform.machine()}')"
EOF
}

# Function to build for specific platform and Python version
build_wheel() {
    local python_version=$1
    local platform=$2
    local platform_tag=${platform//\//_}
    
    print_status "Building wheel for Python ${python_version} on ${platform}..."
    
    # Create output directory
    local output_dir="wheels/${platform_tag}/py${python_version}"
    mkdir -p "${output_dir}"
    
    # Build the wheel
    if docker buildx build \
        --platform="${platform}" \
        --build-arg PYTHON_VERSION="${python_version}" \
        --output type=local,dest="${output_dir}" \
        -f Dockerfile.multiarch \
        . >/dev/null 2>&1; then
        
        print_success "✓ Python ${python_version} on ${platform}"
        return 0
    else
        print_error "✗ Python ${python_version} on ${platform}"
        return 1
    fi
}

# Main function
main() {
    echo "========================================"
    echo "   httpit Docker Cross-Platform Builder"
    echo "   Copyright (c) RODMENA LIMITED"
    echo "========================================"
    echo ""
    
    # Check Docker availability
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker buildx version &> /dev/null; then
        print_error "Docker buildx is not available"
        exit 1
    fi
    
    # Clean up previous builds
    print_status "Cleaning up previous builds..."
    rm -rf wheels/ dist/ Dockerfile.multiarch
    
    # Create Dockerfile
    print_status "Creating multi-architecture Dockerfile..."
    create_dockerfile
    
    # Create and use buildx builder
    print_status "Setting up Docker buildx..."
    docker buildx create --name httpit-multiarch --use --bootstrap >/dev/null 2>&1 || \
    docker buildx use httpit-multiarch >/dev/null 2>&1
    
    # Build for all combinations
    local total_builds=0
    local successful_builds=0
    
    for python_version in "${PYTHON_VERSIONS[@]}"; do
        for platform in "${PLATFORMS[@]}"; do
            ((total_builds++))
            if build_wheel "${python_version}" "${platform}"; then
                ((successful_builds++))
            fi
        done
    done
    
    # Collect all wheels
    print_status "Collecting wheels..."
    mkdir -p dist/
    find wheels/ -name "*.whl" -exec cp {} dist/ \; 2>/dev/null || true
    
    # Show results
    echo ""
    print_status "Build Summary:"
    echo "  Total attempts: ${total_builds}"
    echo "  Successful: ${successful_builds}"
    echo "  Failed: $((total_builds - successful_builds))"
    echo ""
    
    if [ -d "dist" ] && [ "$(ls -A dist/*.whl 2>/dev/null)" ]; then
        print_success "Built wheels:"
        ls -la dist/*.whl | while read -r line; do
            echo "  $line"
        done
        echo ""
        
        # Show wheel details
        print_status "Wheel details:"
        for wheel in dist/*.whl; do
            if [[ -f "$wheel" ]]; then
                basename "$wheel"
            fi
        done
    else
        print_error "No wheels were built successfully"
        exit 1
    fi
    
    # Cleanup
    print_status "Cleaning up..."
    rm -rf wheels/ Dockerfile.multiarch
    docker buildx rm httpit-multiarch >/dev/null 2>&1 || true
    
    echo ""
    print_success "Docker build completed!"
    print_status "Wheels are ready in dist/ directory"
}

# Handle script interruption
trap 'print_error "Build interrupted"; rm -rf wheels/ Dockerfile.multiarch; docker buildx rm httpit-multiarch >/dev/null 2>&1 || true; exit 1' INT TERM

# Run main function
main "$@"