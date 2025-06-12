# Build and Publish Guide

This guide explains how to use the automated build and publish script for httpit.

## Prerequisites

1. **Python Versions**: Install Python 3.9, 3.10, 3.11, 3.12, and/or 3.13
   ```bash
   # On macOS with Homebrew
   brew install python@3.9 python@3.10 python@3.11 python@3.12 python@3.13
   
   # On Ubuntu/Debian
   sudo apt-get install python3.9 python3.10 python3.11 python3.12 python3.13
   ```

2. **C Compiler**: Ensure you have a C compiler for building webfsd
   ```bash
   # macOS
   xcode-select --install
   
   # Ubuntu/Debian
   sudo apt-get install build-essential
   ```

3. **PyPI Account and Token**:
   - Create account at https://pypi.org
   - Generate API token at https://pypi.org/manage/account/token/

## Quick Usage

### Build and Publish to PyPI
```bash
./build_and_publish.sh
```

### Cross-Platform Docker Build (Recommended for Distribution)
```bash
./build_and_publish.sh --docker
```

### Professional Wheel Building with cibuildwheel
```bash
./build_and_publish.sh --cibuildwheel
```

### Test with TestPyPI First (Recommended)
```bash
./build_and_publish.sh --test-pypi
```

### Only Build (No Publish)
```bash
./build_and_publish.sh --skip-publish
```

### Docker-Only Build (Standalone)
```bash
./docker_build.sh
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--skip-cleanup` | Skip the cleanup step |
| `--skip-build` | Skip the build step |
| `--skip-publish` | Skip the publish step |
| `--test-pypi` | Publish to TestPyPI instead of PyPI |
| `--docker` | Use Docker for cross-platform wheel building |
| `--cibuildwheel` | Use cibuildwheel for professional wheel building |
| `--help`, `-h` | Show help message |

## Environment Variables

For automated publishing, set these environment variables:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here
```

Or create a `.env` file:
```bash
# .env file
TWINE_USERNAME=__token__
TWINE_PASSWORD=pypi-your-token-here
```

Then source it:
```bash
source .env
./build_and_publish.sh
```

## What the Script Does

1. **Cleanup**: Removes old build artifacts and temporary files
2. **Build C Extension**: Compiles the webfsd binary
3. **Build Method Selection**:
   - **Default**: Creates virtual environments for each Python version (3.9-3.13)
   - **Docker**: Uses Docker for cross-platform builds (Linux ARM64 + x86_64)
   - **cibuildwheel**: Professional wheel building for multiple platforms
4. **Build Wheels**: Creates wheel files for target platforms and Python versions
5. **Build Source Distribution**: Creates the source tarball
6. **Integrity Check**: Validates all packages with twine
7. **Publish**: Uploads to PyPI or TestPyPI

## Build Methods Comparison

| Method | Platforms | Architectures | Python Versions | Requirements |
|--------|-----------|---------------|----------------|--------------|
| **Default** | Host OS | Host arch | Locally installed | Python 3.9-3.13 |
| **Docker** | Linux | x86_64, ARM64 | All versions | Docker + buildx |
| **cibuildwheel** | Linux, macOS, Windows | All supported | All versions | Docker (for Linux) |

## Examples

### Full Build and Publish Workflow
```bash
# 1. Test build first (local)
./build_and_publish.sh --skip-publish

# 2. Build with Docker for cross-platform
./build_and_publish.sh --docker --skip-publish

# 3. Test publish to TestPyPI
./build_and_publish.sh --docker --test-pypi

# 4. Publish to real PyPI
./build_and_publish.sh --docker
```

### Cross-Platform Production Build
```bash
# Build for Linux ARM64 + x86_64 with all Python versions
./build_and_publish.sh --docker --skip-publish

# Or use the standalone Docker builder
./docker_build.sh
```

### CI/CD Optimized Build
```bash
# Professional wheel building (recommended for CI)
./build_and_publish.sh --cibuildwheel
```

### CI/CD Pipeline
```bash
# Set credentials
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=$PYPI_TOKEN

# Build and publish
./build_and_publish.sh
```

### Development Workflow
```bash
# Build only for testing
./build_and_publish.sh --skip-publish

# Check what was built
ls -la dist/

# Test install locally
pip install dist/httpit-*.whl
```

## Troubleshooting

### Missing Python Versions
If some Python versions are missing, the script will skip them and continue with available versions.

### Build Failures
- Ensure C compiler is installed
- Check that `make` command works
- Verify all dependencies are installed

### Publish Failures
- Check your PyPI token is correct
- Ensure package name doesn't conflict
- Try TestPyPI first: `--test-pypi`

### Cleanup Issues
If you need to force cleanup:
```bash
rm -rf build/ dist/ *.egg-info/ build_venvs/
make clean
```

## Advanced Usage

### Custom Python Versions
Edit the script to modify the `PYTHON_VERSIONS` array:
```bash
PYTHON_VERSIONS=("3.9" "3.11" "3.12")  # Only specific versions
```

### Custom Build Directory
Modify `VENV_BASE_DIR` in the script:
```bash
VENV_BASE_DIR="custom_build_dir"
```

## Security Notes

- Never commit PyPI tokens to version control
- Use project-scoped tokens when possible
- Consider using GitHub Actions for automated publishing
- Test with TestPyPI before publishing to real PyPI

## Support

For issues with the build script or httpit package:
- Create an issue at: https://github.com/rodmena-limited/fasthttp/issues
- Contact: info@rodmena.co.uk
- Visit: https://rodmena.co.uk