#!/bin/bash
set -e

# Test building with different Python versions using uv

echo "Testing uv build for multiple Python versions..."

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Test Python versions
VERSIONS=("3.9" "3.10" "3.11" "3.12" "3.13")

for version in "${VERSIONS[@]}"; do
    echo ""
    echo "=========================================="
    echo "Testing Python $version"
    echo "=========================================="
    
    # Install Python version if needed
    echo "Installing Python $version..."
    uv python install $version
    
    # Check Python version
    echo "Checking Python version..."
    uv run --python $version python --version
    
    # Create isolated project directory
    project_dir="test_py${version}"
    rm -rf $project_dir
    mkdir -p $project_dir
    cd $project_dir
    
    # Copy project files
    cp -r ../fasthttp ../setup.py ../pyproject.toml ../README.md ../webfsd . 2>/dev/null || true
    cp -r ../src . 2>/dev/null || true
    cp ../GNUmakefile . 2>/dev/null || true
    
    # Install build dependencies
    echo "Installing build dependencies..."
    uv pip install --python $version build
    
    # Build wheel
    echo "Building wheel..."
    uv run --python $version python -m build --wheel --outdir wheel_output/
    
    # Show what was built
    echo "Built wheels:"
    ls -la wheel_output/*.whl 2>/dev/null || echo "No wheels found"
    
    # Go back to main directory
    cd ..
done

echo ""
echo "=========================================="
echo "Summary of built wheels:"
echo "=========================================="
for version in "${VERSIONS[@]}"; do
    project_dir="test_py${version}"
    if [ -d "$project_dir/wheel_output" ]; then
        echo "Python $version:"
        ls -la $project_dir/wheel_output/*.whl 2>/dev/null || echo "  No wheels found"
    fi
done