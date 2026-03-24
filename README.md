# 🤖 SyntaxLens - 智能屏幕取词与语法分析助手

<div align="center">
  <img src="app.ico" width="128" height="128" alt="SyntaxLens Icon">
  <br>
  <br>
  
  ![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
  ![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?style=flat-square&logo=qt)
  ![Architecture](https://img.shields.io/badge/Arch-Queue%20%2B%20IPC-orange?style=flat-square)
  ![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows)
  ![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

  **"不仅是翻译，更是你的私人 AI 语言私教。"**
  
  [下载最新版 (v0.2.0)](https://github.com/Xie-free/SyntaxLens/releases) | [查看更新日志](#-更新日志--changelog)
</div>

---

## 📖 简介 | Introduction

**SyntaxLens** 是一款专为 Windows 用户打造的高性能全局屏幕取词工具。

它采用了 **底层 Windows API 硬件级模拟** 技术，能够穿透记事本、IDE（如 PyCharm/VSCode）、PDF 阅读器等通常难以取词的软件，实现**一键全行选中**。

在 **v0.2.0** 版本中，我们重构了核心架构，引入了 **延迟加载 (Lazy Loading)** 和 **消息队列 (Message Queue)** 机制，彻底解决了启动慢和系统兼容性问题，为您提供“秒开、秒回、永不闪退”的极致体验。

## ✨ 核心功能 | Features

- **⚡ 极速启动 (Lazy Loading)**：
  采用智能延迟加载策略，软件冷启动时间压缩至毫秒级。仅在首次调用 AI 时加载重型依赖，实现“即点即用”。

- **🛡️ 稳如磐石的架构**：
  基于 **Queue (消息队列)** 隔离了底层键盘钩子与 UI 线程，并引入 **IPC (进程间通信)** 机制。彻底杜绝了 `0xC0000409` 等常见的 Windows 钩子冲突崩溃，支持单例运行与唤醒。

- **🌑 沉浸式深色体验**：
  - 全新设计的 **深色磨砂 UI**，代码高亮配色参考 VS Code Dark 主题。
  - **流式响应 (Streaming)**：类似 ChatGPT 的打字机效果，实时渲染 Markdown 格式（标题、加粗、代码块），阅读体验丝滑。

- **⌨️ 智能防误触录制**：
  设置界面新增 **按键录制组件**，直接按下键盘即可设置快捷键，杜绝拼写错误。录制期间自动屏蔽全局触发，防止误操作。

- **👻 静默守护**：
  支持开机自启并最小化到托盘。启动参数支持 `--silent` 模式，开机后自动潜伏在后台，不弹出主窗口打扰工作。

## 📸 截图展示 | Screenshots

### 1. 沉浸式 AI 分析 (Markdown 渲染)
> 
![Popup Example](https://img.illusionlie.com/file/1768483282275.png)

### 2. 智能化设置面板 (支持按键录制)
> 
![Settings Example](https://img.illusionlie.com/file/1768483413001.png)

## 🚀 快速开始 | Quick Start

### 方式一：直接运行 (推荐)
1. 在右侧 **[Releases]** 页面下载最新的 `SyntaxLens.exe`。
2. 双击运行（支持开机自启）。
3. 在设置面板填入你的 API Key (支持 DeepSeek, OpenAI, Kimi 等)。
4. 选中任意文本，按下 **`F9`** (语法分析) 或 **`Ctrl+T`** (翻译)。

### 方式二：源码构建 (开发者)
如果你想自己修改代码：

```bash
# 1. 克隆仓库
git clone https://github.com/Xie-free/SyntaxLens.git
cd SyntaxLens

# 2. 安装依赖 (仅需核心库)
pip install -r requirements.txt

# 3. 运行
python main.py

# 4. 打包 (推荐文件夹模式，启动最快)
pyinstaller --noconsole --onedir --name "SyntaxLens" --icon="app.ico" --add-data "app.ico;." --clean main.py
```
📝 更新日志 | Changelog
v0.2.0 (Stable)

    🔥 重构：引入消息队列机制，彻底解决键盘钩子导致的闪退问题。

    ⚡ 优化：实现 Lazy Import，启动速度提升 80%。

    🎨 UI：新增深色磨砂弹窗，支持 Markdown 流式渲染与滚动条自动适应。

    🛠️ 功能：新增快捷键录制功能、IPC 单例唤醒、静默启动参数。

    🗑️ 瘦身：移除 pyautogui 等冗余依赖，体积更小。

v0.1.0 (Initial)

    🎉 项目初次发布。

    支持全局硬件取词与 AI 基础调用。

<div align="center">
Made with ❤️ by Xie-free(Powered by AI)
</div>
