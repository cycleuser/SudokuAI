#!/bin/bash
# PyPI upload script for Unix/Linux/macOS

set -e

echo "Building SudokuAI package..."
rm -rf dist/ build/ *.egg-info
/Users/fred/miniconda3/envs/dev/bin/python -m pip install --upgrade build twine
/Users/fred/miniconda3/envs/dev/bin/python -m build

echo ""
echo "Package built. Contents:"
ls -la dist/

echo ""
echo "To upload to PyPI, run:"
echo "  /Users/fred/miniconda3/envs/dev/bin/python -m twine upload dist/*"
echo ""
echo "To upload to TestPyPI, run:"
echo "  /Users/fred/miniconda3/envs/dev/bin/python -m twine upload --repository testpypi dist/*"