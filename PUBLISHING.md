# Publishing httpit to PyPI

## Prerequisites

1. **PyPI Account**: Create an account at https://pypi.org
2. **API Token**: Generate an API token at https://pypi.org/manage/account/token/
3. **Install Tools**:
   ```bash
   pip install --upgrade pip build twine
   ```

## Building the Package

1. **Clean previous builds**:
   ```bash
   rm -rf dist/ build/ *.egg-info
   ```

2. **Build the wheel and source distribution**:
   ```bash
   python -m build
   ```

   This creates:
   - `dist/httpit-1.21.0-*.whl` (wheel file)
   - `dist/httpit-1.21.0.tar.gz` (source distribution)

## Publishing to PyPI

### Option 1: Using API Token (Recommended)

1. **Set up your PyPI token**:
   ```bash
   # Create ~/.pypirc file
   cat > ~/.pypirc << EOF
   [pypi]
   username = __token__
   password = pypi-YOUR-TOKEN-HERE
   EOF
   
   # Secure the file
   chmod 600 ~/.pypirc
   ```

2. **Upload to PyPI**:
   ```bash
   python -m twine upload dist/*
   ```

### Option 2: Using Environment Variables

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR-TOKEN-HERE
python -m twine upload dist/*
```

### Option 3: Interactive Login

```bash
python -m twine upload dist/*
# Enter __token__ as username
# Enter your token as password
```

## Testing with TestPyPI (Recommended First)

1. **Upload to TestPyPI**:
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

2. **Test installation**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ httpit
   ```

## Verification

After publishing, verify your package:

```bash
# Wait a few minutes for PyPI to update
pip install httpit
python -c "import httpit; print(httpit.__version__)"
```

## Common Issues

### "Package already exists"
- You can't upload the same version twice
- Increment version in `pyproject.toml` and rebuild

### Authentication Failed
- Make sure username is `__token__` (not your PyPI username)
- Check your API token starts with `pypi-`
- Verify token has upload permissions for this project

### Missing Dependencies
```bash
pip install --upgrade setuptools wheel twine build
```

## Quick Commands for Publishing

```bash
# Full process
make clean
python -m build
python -m twine check dist/*  # Verify package
python -m twine upload dist/*

# Or if you have a Makefile target
make publish
```

## Security Notes

- Never commit `.pypirc` to version control
- Use project-scoped tokens when possible
- Consider using GitHub Actions for automated publishing
- Delete old tokens after rotating