# SudokuAI 数独LLM评测平台

一个用于大语言模型推理能力评测的数独游戏平台，支持多难度等级生成、多LLM提供商接入，以及完整的性能报告生成。

## 项目背景

SudokuAI 的开发源于对大语言模型(LLM)推理能力进行系统性评估的迫切需求。传统的评测基准主要关注知识检索和文本生成能力，而数独谜题提供了一个受控环境，可以精确评估逻辑推理、约束满足和问题解决能力。

该平台的开发基于研究发现：即使 LLM 在模式识别和语言理解方面表现出色，它们在需要系统性逻辑推导的任务上仍面临挑战。通过提供标准化的框架让 LLM 解决数独谜题，SudokuAI 使研究人员和开发者能够：

1. 量化测量不同模型架构的推理性能
2. 比较逐步推理与一次性解答两种方法的效率
3. 评估随着问题复杂度增加时的性能衰减
4. 生成详细报告以支持可重复的基准测试

平台通过 OpenAI 兼容 API 支持多个 LLM 提供商，包括 Ollama（本地推理）、阿里云百炼、MiniMax、OpenAI 等，使用统一接口即可评测不同来源的模型。

## 应用场景

SudokuAI 在研究、教育和开发领域具有多种应用场景：

**LLM 评测与基准测试**
研究人员可以使用 SudokuAI 评估和比较不同 LLM 的推理能力。平台提供标准化指标，包括正确率、步数效率和用时表现。跨多个难度等级的批量评测可实现全面的基准测试。

**教育工具**
教育工作者可利用 SudokuAI 展示 AI 推理过程。逐步模式显示 LLM 如何处理逻辑问题，让学生了解模型的问题解决策略，并可将自身推理与 LLM 输出进行对比。

**LLM 开发与调试**
开发 LLM 应用的开发者可以将 SudokuAI 作为提示工程和推理链优化的测试平台。每一步移动的详细日志有助于识别模型在何处出错及其原因。

**持续集成测试**
CLI 接口支持将数独谜题集成到 CI/CD 流水线中，实现 LLM 推理能力的自动化长期跟踪测试。

## 兼容硬件

SudokuAI 设计为在广泛的硬件配置上高效运行。

**最低要求**
- CPU：任何现代 x86_64 或 ARM64 处理器
- 内存：2 GB 可用内存
- 存储：100 MB 磁盘空间
- 网络：可选（仅远程 LLM API 需要）

**推荐配置**
- CPU：多核处理器，适合批量评测
- 内存：4 GB 或更多
- 存储：推荐 SSD 以加快日志访问

**GPU 支持**
SudokuAI 本身不需要 GPU，但通过 Ollama 进行本地 LLM 推理可从 GPU 加速中受益。本地模型最佳性能配置：
- NVIDIA GPU：6+ GB 显存可运行 4B 模型
- Apple Silicon Mac：Metal 加速表现优异

**特别说明**
- 使用远程 LLM API（OpenAI、阿里云、MiniMax）时，网络延迟会影响评测时间
- 通过 Ollama 进行本地推理需要足够内存加载模型
- GUI 模式需要显示器；CLI 和 Web 模式可在无头环境中运行

## 操作系统

SudokuAI 以跨平台兼容性为核心设计原则。

**Windows**
完全兼容 Windows 10 和 Windows 11。通过 pip 安装即可正常工作。GUI 通过 PySide6 使用原生 Windows 样式。PowerShell 和命令提示符均支持 CLI 接口。

**macOS**
支持 macOS 10.15 (Catalina) 及更高版本。通过 PySide6 的 ARM64 支持在 Apple Silicon (M1/M2/M3) 上实现原生性能。CLI 在 Terminal 和 iTerm2 中均可运行。

**Linux**
兼容主流发行版，包括 Ubuntu 20.04+、Debian 11+、Fedora 35+ 和 Arch Linux。服务器部署可使用 CLI 或 Web 接口，无需显示器。可创建 systemd 服务文件将 Web 服务器作为守护进程运行。

**平台特定说明**
- Linux 上需确保已安装 Qt 依赖以支持 GUI 功能
- macOS 首次启动可能需要在安全设置中允许应用运行
- Windows 上某些杀毒软件可能需要为 Python 可执行文件添加例外

## 依赖环境

SudokuAI 需要 Python 3.10 或更高版本及若干外部包。

**核心依赖**
- `openai` (≥1.0.0)：OpenAI 兼容 API 客户端，用于 LLM 集成
- `PySide6` (≥6.5.0)：基于 Qt 的 GUI 框架，提供跨平台界面
- `Flask` (≥3.0.0)：Web 框架，用于 Web 界面和 REST API
- `requests` (≥2.28.0)：HTTP 库，用于 API 通信

**可选依赖**
- `pytest` (≥7.0.0)：测试框架，用于运行测试套件
- `black` (≥23.0.0)：代码格式化工具
- `mypy` (≥1.0.0)：静态类型检查器

**依赖选择原因**
- PySide6 选中是因为跨平台原生外观
- Flask 提供轻量级 Web 服务器，无重依赖
- OpenAI SDK 通过标准化 API 格式实现多 LLM 提供商兼容

## 安装过程

**方法一：从 PyPI 安装（推荐）**

```bash
pip install sudokuai
```

验证安装：

```bash
sudokuai -V
```

**方法二：从源码安装**

```bash
git clone https://github.com/user/sudokuai.git
cd sudokuai
pip install -e .
```

**方法三：使用 Conda**

```bash
conda create -n sudokuai python=3.10
conda activate sudokuai
pip install sudokuai
```

**安装后设置**

安装完成后，配置 LLM 提供商。本地 Ollama：

```bash
# 确保 Ollama 正在运行
ollama serve

# 拉取模型
ollama pull gemma3:4b
```

云服务提供商需配置 API 密钥：

```bash
sudokuai config add --name myprovider --provider openai --api-base https://api.openai.com/v1 --model gpt-4 --api-key sk-xxx
```

## 使用方法

**图形用户界面 (GUI)**

```bash
sudokuai          # 启动 GUI（默认）
sudokuai gui      # 显式 GUI 模式
```

GUI 提供交互式数独棋盘、LLM 配置面板和实时评测日志。

**Web 界面**

```bash
sudokuai web --port 5000
# 在浏览器打开 http://localhost:5000
```

**命令行界面 (CLI)**

```bash
# 生成谜题
sudokuai generate -d medium -o puzzle.json

# 求解谜题
sudokuai solve puzzle.json -o solution.json

# 验证解答
sudokuai validate solution.json

# 让 LLM 玩游戏
sudokuai play -m gemma3:4b -d easy --mode oneshot

# 评测 LLM 性能
sudokuai evaluate -m gemma3:4b --games 5 --difficulties easy,medium

# 生成报告
sudokuai report evaluation.json -o report.md

# 配置提供商
sudokuai config list
sudokuai config add --name local --provider ollama --api-base http://localhost:11434/v1 --model llama3
```

**统一标志**
所有接口支持标准标志：
- `-V, --version`：显示版本
- `-v, --verbose`：启用详细输出
- `-o, --output`：指定输出路径
- `--json`：以 JSON 格式输出
- `-q, --quiet`：抑制非必要输出

## 运行截图

| GUI 界面 | Web 界面 |
|:--------:|:--------:|
| ![GUI](images/gui.png) | ![Web](images/web.png) |

**GUI 界面说明**
主窗口包含清晰标注 3×3 宫格的 9×9 数独棋盘。左侧面板包含游戏控制和 LLM 配置选项。底部面板显示带时间戳的评测日志。

**Web 界面说明**
Web 界面采用响应式设计，功能与 GUI 相同。活动日志在 LLM 评测期间显示实时进度。

## 授权协议

SudokuAI 采用 GNU 通用公共许可证第三版 (GPLv3) 发布。

**主要权利**
- 为任何目的使用该软件的自由
- 研究和修改源代码的自由
- 再分发副本的自由
- 发布修改版本的自由

**要求**
- 衍生作品必须以 GPLv3 许可
- 发行时必须提供源代码
- 必须保留许可证和版权声明

完整许可证文本见 [LICENSE](LICENSE) 文件。