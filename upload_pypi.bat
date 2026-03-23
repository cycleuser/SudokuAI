@echo off
REM PyPI upload script for Windows

echo Building SudokuAI package...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.egg-info rmdir /s /q *.egg-info

python -m pip install --upgrade build twine
python -m build

echo.
echo Package built. Contents:
dir dist

echo.
echo To upload to PyPI, run:
echo   python -m twine upload dist/*
echo.
echo To upload to TestPyPI, run:
echo   python -m twine upload --repository testpypi dist/*