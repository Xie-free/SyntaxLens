# 🤖 SyntaxLens - 智能屏幕取词与语法分析助手

<div align="center">
  <img src="app.png" width="128" height="128" alt="SyntaxLens Icon">
  <br>
  
  ![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
  ![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
  ![Platform](https://img.shields.io/badge/Platform-Windows-0078D6)
  ![License](https://img.shields.io/badge/License-MIT-orange)

  **"不仅是翻译，更是你的私人 AI 语言私教。"**
</div>

## 📖 简介 | Introduction

**SyntaxLens** 是一款专为 Windows 用户打造的全局屏幕取词工具。

与传统的划词翻译软件不同，SyntaxLens 采用了 **底层 Windows API 硬件级模拟** 技术，能够穿透记事本、IDE（如 PyCharm/VSCode）、PDF 阅读器等通常难以取词的软件，实现**一键全行选中**。

结合 DeepSeek、火山引擎（豆包）等强大的 AI 模型，它不仅能翻译，还能深度分析句子的语法结构，指出语病并提供修改建议。

## ✨ 核心功能 | Features

- **⚡ 硬件级暴力取词**：
  使用 `ctypes` 调用 `user32.dll` 进行硬件扫描码模拟，解决光标乱跳、无法选中的痛点。支持自动判断：若用户未手动选词，自动全选当前行。

- **🧠 双模式 AI 引擎**：
  - **F9 (默认)**：**语法分析模式**。拆解句子主谓宾，由 AI 诊断语病并生成 HTML 可视化报告。
  - **Ctrl+T (默认)**：**中英互译模式**。地道的中英互译，附带生僻词备注。

- **🎨 现代化 GUI 配置**：
  - 拒绝繁琐的配置文件修改，提供直观的设置面板。
  - 支持自定义 API Key、模型 Endpoint、Base URL。
  - 支持 **热重载**：修改快捷键无需重启软件。

- **🛡️ 极简后台运行**：
  - 支持最小化到系统托盘，点击 `×` 可选择后台静默运行。
  - 极低的内存占用，不打扰日常工作。

## 📸 截图展示 | Screenshots

### 1. 语法分析结果
![Popup Example](https://img.illusionlie.com/file/1768483282275.png)

### 2. 设置面板
![Settings Example](https://img.illusionlie.com/file/1768483413001.png)

## 🚀 快速开始 | Quick Start

### 方式一：直接运行 (推荐普通用户)
1. 在右侧 **[Releases]** 页面下载最新的 `SyntaxLens.exe`。
2. 双击运行，软件会自动弹出设置窗口。
3. 填入你的 API Key (推荐使用 DeepSeek 或 火山引擎)。
4. 点击保存，即可开始使用！

### 方式二：源码运行 (推荐开发者)
如果你想自己修改代码：

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/SyntaxLens.git
cd SyntaxLens

# 2. 创建虚拟环境 (可选但推荐)
python -m venv .venv
# Windows 激活虚拟环境:
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行
python main.py
