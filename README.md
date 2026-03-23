# SudokuAI

A Sudoku game platform for LLM evaluation, featuring puzzle generation, multiple difficulty levels, and comprehensive LLM performance benchmarking.

## Project Background

SudokuAI was developed to address the growing need for systematic evaluation of Large Language Model (LLM) reasoning capabilities. While traditional benchmarks focus on knowledge retrieval and text generation, Sudoku puzzles provide a controlled environment to assess logical reasoning, constraint satisfaction, and problem-solving abilities.

The development of this platform stems from research indicating that LLMs often struggle with tasks requiring systematic logical deduction, even when they excel at pattern recognition and language understanding. By providing a standardized framework for LLMs to solve Sudoku puzzles, SudokuAI enables researchers and developers to:

1. Quantitatively measure reasoning performance across different model architectures
2. Compare step-by-step reasoning versus one-shot problem solving approaches
3. Evaluate performance degradation as problem complexity increases
4. Generate detailed reports for reproducible benchmarking

The platform supports multiple LLM providers through OpenAI-compatible APIs, making it easy to evaluate models from Ollama (local inference), Alibaba Cloud, MiniMax, OpenAI, and other providers using a unified interface.

## Application Scenarios

SudokuAI serves multiple application scenarios across research, education, and development:

**LLM Evaluation and Benchmarking**
Researchers can use SudokuAI to evaluate and compare the reasoning capabilities of different LLMs. The platform provides standardized metrics including accuracy, move efficiency, and time performance. Batch evaluation across multiple difficulty levels enables comprehensive benchmarking.

**Educational Tools**
Educators can utilize SudokuAI to demonstrate AI reasoning processes. The step-by-step mode shows how LLMs approach logical problems, providing insights into their problem-solving strategies. Students can compare their own reasoning with LLM outputs.

**LLM Development and Debugging**
Developers working on LLM applications can use SudokuAI as a testbed for prompt engineering and reasoning chain optimization. The detailed logging of each move helps identify where models make errors and why.

**Continuous Integration Testing**
The CLI interface enables integration of Sudoku puzzles into CI/CD pipelines for automated testing of LLM reasoning capabilities over time.

## Hardware Compatibility

SudokuAI is designed to run efficiently on a wide range of hardware configurations.

**Minimum Requirements**
- CPU: Any modern x86_64 or ARM64 processor
- RAM: 2 GB available memory
- Storage: 100 MB disk space
- Network: Optional (only required for remote LLM APIs)

**Recommended Configuration**
- CPU: Multi-core processor for batch evaluations
- RAM: 4 GB or more
- Storage: SSD recommended for faster log access

**GPU Support**
While SudokuAI itself does not require GPU, local LLM inference through Ollama can benefit from GPU acceleration. For optimal performance with local models:
- NVIDIA GPU with 6+ GB VRAM for 4B models
- Apple Silicon Macs work well with Metal acceleration

**Special Considerations**
- When using remote LLM APIs (OpenAI, Aliyun, MiniMax), network latency will affect evaluation times
- Local inference with Ollama requires sufficient RAM for model loading
- GUI mode requires a display; CLI and Web modes work in headless environments

## Operating Systems

SudokuAI is developed with cross-platform compatibility as a core design principle.

**Windows**
Fully compatible with Windows 10 and Windows 11. Installation via pip works seamlessly. The GUI uses native Windows styling through PySide6. PowerShell and Command Prompt both support the CLI interface.

**macOS**
Supports macOS 10.15 (Catalina) and later. Native performance on Apple Silicon (M1/M2/M3) through PySide6's ARM64 support. The CLI works in both Terminal and iTerm2.

**Linux**
Compatible with major distributions including Ubuntu 20.04+, Debian 11+, Fedora 35+, and Arch Linux. Server deployments can use the CLI or Web interfaces without requiring a display. Systemd service files can be created for running the web server as a daemon.

**Platform-Specific Notes**
- On Linux, ensure Qt dependencies are installed for GUI functionality
- On macOS, you may need to allow the application in Security settings on first launch
- On Windows, some antivirus software may require an exception for the Python executable

## Dependencies

SudokuAI requires Python 3.10 or higher and several external packages.

**Core Dependencies**
- `openai` (≥1.0.0): OpenAI-compatible API client for LLM integration
- `PySide6` (≥6.5.0): Qt-based GUI framework for cross-platform interfaces
- `Flask` (≥3.0.0): Web framework for the web interface and REST API
- `requests` (≥2.28.0): HTTP library for API communications

**Optional Dependencies**
- `pytest` (≥7.0.0): Testing framework for running the test suite
- `black` (≥23.0.0): Code formatter for development
- `mypy` (≥1.0.0): Static type checker

**Why These Dependencies**
- PySide6 was chosen for native look-and-feel across platforms
- Flask provides a lightweight web server without heavy dependencies
- The OpenAI SDK enables compatibility with multiple LLM providers through their standardized API format

## Installation

**Method 1: Install from PyPI (Recommended)**

```bash
pip install sudokuai
```

Verify the installation:

```bash
sudokuai -V
```

**Method 2: Install from Source**

```bash
git clone https://github.com/user/sudokuai.git
cd sudokuai
pip install -e .
```

**Method 3: Using Conda**

```bash
conda create -n sudokuai python=3.10
conda activate sudokuai
pip install sudokuai
```

**Post-Installation Setup**

After installation, configure your LLM providers. For local Ollama:

```bash
# Ensure Ollama is running
ollama serve

# Pull a model
ollama pull gemma3:4b
```

For cloud providers, set up API keys:

```bash
sudokuai config add --name myprovider --provider openai --api-base https://api.openai.com/v1 --model gpt-4 --api-key sk-xxx
```

## Usage

**Graphical User Interface (GUI)**

```bash
sudokuai          # Launch GUI (default)
sudokuai gui      # Explicit GUI mode
```

The GUI provides an interactive Sudoku board, LLM configuration panel, and real-time evaluation logging.

**Web Interface**

```bash
sudokuai web --port 5000
# Open http://localhost:5000 in your browser
```

**Command-Line Interface (CLI)**

```bash
# Generate a puzzle
sudokuai generate -d medium -o puzzle.json

# Solve a puzzle
sudokuai solve puzzle.json -o solution.json

# Validate a solution
sudokuai validate solution.json

# Let LLM play
sudokuai play -m gemma3:4b -d easy --mode oneshot

# Evaluate LLM performance
sudokuai evaluate -m gemma3:4b --games 5 --difficulties easy,medium

# Generate a report
sudokuai report evaluation.json -o report.md

# Configure providers
sudokuai config list
sudokuai config add --name local --provider ollama --api-base http://localhost:11434/v1 --model llama3
```

**Unified Flags**
All interfaces support standard flags:
- `-V, --version`: Display version
- `-v, --verbose`: Enable verbose output
- `-o, --output`: Specify output path
- `--json`: Output in JSON format
- `-q, --quiet`: Suppress non-essential output

## Screenshots

| GUI Interface | Web Interface |
|:-------------:|:-------------:|
| ![GUI](images/gui.png) | ![Web](images/web.png) |

**GUI Interface Description**
The main window features a 9x9 Sudoku grid with clearly marked 3x3 boxes. The left panel contains game controls and LLM configuration options. The bottom panel shows the evaluation log with timestamps.

**Web Interface Description**
The web interface mirrors GUI functionality with a responsive design. The activity log shows real-time progress during LLM evaluation.

## License

SudokuAI is released under the GNU General Public License version 3 (GPLv3).

**Key Rights**
- Freedom to use the software for any purpose
- Freedom to study and modify the source code
- Freedom to redistribute copies
- Freedom to distribute modified versions

**Requirements**
- Derivative works must be licensed under GPLv3
- Source code must be made available upon distribution
- License and copyright notices must be preserved

See the [LICENSE](LICENSE) file for the complete license text.