<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="License">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey.svg" alt="Platform">
</p>

<p align="center">
  <a href="#简体中文">简体中文</a> | 
  <a href="#繁體中文">繁體中文</a> | 
  <a href="#english">English</a>
</p>

---

<a name="简体中文"></a>
# 🚀 ProcPilot - 轻量级终端进程智能管理器

## 🎉 项目介绍

**ProcPilot** 是一款零依赖、跨平台的终端进程智能管理工具，专为开发者和系统管理员设计。它提供了实时进程监控、资源分析、进程树可视化、智能告警等强大功能，帮助您轻松掌控系统进程状态。

### 💡 灵感来源

在日常开发和运维工作中，我们经常需要监控系统进程、排查资源占用问题。现有的工具要么功能过于复杂，要么依赖众多第三方库。ProcPilot 应运而生——它专注于提供**轻量、高效、零依赖**的进程管理体验。

### ✨ 核心特性

- 🔍 **实时进程监控** - 实时追踪CPU、内存使用情况
- 🌳 **进程树可视化** - 直观展示进程父子关系
- 🚨 **智能告警系统** - 自动检测资源异常并告警
- 🏷️ **标签与分组** - 灵活组织和管理进程
- 📊 **资源分析报告** - 一键导出详细报告
- 💻 **美观TUI界面** - 终端交互式操作界面
- ⚡ **零依赖** - 纯Python标准库实现
- 🌍 **跨平台支持** - Linux / macOS / Windows

---

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- 支持 Linux、macOS、Windows

### 安装

```bash
# 从 PyPI 安装
pip install procpilot

# 或从源码安装
git clone https://github.com/gitstq/procpilot.git
cd procpilot
pip install -e .
```

### 基本使用

```bash
# 启动交互式TUI界面
procpilot

# 列出所有进程
procpilot list

# 按CPU排序显示前10个进程
procpilot top -n 10

# 显示进程树
procpilot tree

# 搜索进程
procpilot search python

# 查看进程详情
procpilot info 1234

# 终止进程
procpilot kill 1234

# 导出报告
procpilot export report.json
```

---

## 📖 详细使用指南

### 交互式TUI界面

运行 `procpilot` 命令启动交互式界面：

| 快捷键 | 功能 |
|--------|------|
| `↑/↓` | 上下移动选择 |
| `PgUp/PgDn` | 翻页 |
| `k` | 终止选中进程 (SIGTERM) |
| `K` | 强制终止 (SIGKILL) |
| `s` | 暂停进程 |
| `r` | 恢复进程 |
| `t` | 切换树形视图 |
| `/` | 搜索进程 |
| `n` | 切换排序方式 |
| `a` | 查看告警 |
| `Enter` | 查看进程详情 |
| `q` | 退出 |
| `?` | 显示帮助 |

### 命令行参数

#### 列出进程

```bash
# 基本列表
procpilot list

# 按内存排序
procpilot list --sort memory

# 过滤进程
procpilot list --filter python

# JSON格式输出
procpilot list --json
```

#### 进程树

```bash
# 显示完整进程树
procpilot tree

# 指定根进程
procpilot tree --pid 1

# 限制深度
procpilot tree --depth 3

# 紧凑格式
procpilot tree --compact
```

#### 监控模式

```bash
# 开始监控（默认1秒间隔）
procpilot monitor

# 指定间隔和时长
procpilot monitor --interval 2 --duration 60
```

### 进程标签与分组

```bash
# 添加标签
procpilot tag 1234 web-server

# 移除标签
procpilot tag 1234 web-server --remove

# 设置分组
procpilot group 1234 production
```

---

## 💡 设计思路

### 技术选型

- **零依赖设计**：仅使用Python标准库，确保最大兼容性
- **跨平台实现**：针对Linux(/proc)、macOS(ps命令)、Windows(wmic)分别优化
- **模块化架构**：核心、监控、树、告警模块独立，易于扩展

### 架构图

```
procpilot/
├── core.py      # 进程管理核心
├── monitor.py   # 实时监控
├── tree.py      # 进程树可视化
├── alerts.py    # 智能告警
├── tui.py       # 终端界面
└── cli.py       # 命令行入口
```

### 后续迭代计划

- [ ] 支持网络连接监控
- [ ] 添加进程性能图表
- [ ] 支持远程主机监控
- [ ] Web界面支持
- [ ] 插件系统

---

## 📦 打包与部署

### 构建发布包

```bash
# 安装构建工具
pip install build

# 构建
python -m build

# 生成的包在 dist/ 目录
```

### 打包为可执行文件

```bash
# 使用 PyInstaller
pip install pyinstaller
pyinstaller --onefile procpilot/cli.py --name procpilot
```

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 提交规范

- `feat`: 新功能
- `fix`: 修复问题
- `docs`: 文档更新
- `refactor`: 代码重构
- `test`: 测试相关

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

<a name="繁體中文"></a>
# 🚀 ProcPilot - 輕量級終端進程智能管理器

## 🎉 專案介紹

**ProcPilot** 是一款零依賴、跨平台的終端進程智能管理工具，專為開發者和系統管理員設計。它提供了實時進程監控、資源分析、進程樹視覺化、智能告警等強大功能，幫助您輕鬆掌控系統進程狀態。

### 💡 靈感來源

在日常開發和運維工作中，我們經常需要監控系統進程、排查資源佔用問題。現有的工具要麼功能過於複雜，要麼依賴眾多第三方函式庫。ProcPilot 應運而生——它專注於提供**輕量、高效、零依賴**的進程管理體驗。

### ✨ 核心特性

- 🔍 **實時進程監控** - 實時追蹤CPU、記憶體使用情況
- 🌳 **進程樹視覺化** - 直觀展示進程父子關係
- 🚨 **智能告警系統** - 自動檢測資源異常並告警
- 🏷️ **標籤與分組** - 靈活組織和管理進程
- 📊 **資源分析報告** - 一鍵匯出詳細報告
- 💻 **美觀TUI界面** - 終端互動式操作界面
- ⚡ **零依賴** - 純Python標準函式庫實現
- 🌍 **跨平台支援** - Linux / macOS / Windows

---

## 🚀 快速開始

### 環境要求

- Python 3.8 或更高版本
- 支援 Linux、macOS、Windows

### 安裝

```bash
# 從 PyPI 安裝
pip install procpilot

# 或從源碼安裝
git clone https://github.com/gitstq/procpilot.git
cd procpilot
pip install -e .
```

### 基本使用

```bash
# 啟動互動式TUI界面
procpilot

# 列出所有進程
procpilot list

# 按CPU排序顯示前10個進程
procpilot top -n 10

# 顯示進程樹
procpilot tree

# 搜尋進程
procpilot search python

# 查看進程詳情
procpilot info 1234

# 終止進程
procpilot kill 1234

# 匯出報告
procpilot export report.json
```

---

## 📖 詳細使用指南

### 互動式TUI界面

運行 `procpilot` 命令啟動互動式界面：

| 快捷鍵 | 功能 |
|--------|------|
| `↑/↓` | 上下移動選擇 |
| `PgUp/PgDn` | 翻頁 |
| `k` | 終止選中進程 (SIGTERM) |
| `K` | 強制終止 (SIGKILL) |
| `s` | 暫停進程 |
| `r` | 恢復進程 |
| `t` | 切換樹形視圖 |
| `/` | 搜尋進程 |
| `n` | 切換排序方式 |
| `a` | 查看告警 |
| `Enter` | 查看進程詳情 |
| `q` | 退出 |
| `?` | 顯示幫助 |

---

## 📦 打包與部署

### 構建發布包

```bash
# 安裝構建工具
pip install build

# 構建
python -m build
```

---

## 🤝 貢獻指南

歡迎貢獻代碼、報告問題或提出建議！

1. Fork 本倉庫
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 創建 Pull Request

---

## 📄 開源協議

本專案採用 [MIT License](LICENSE) 開源協議。

---

<a name="english"></a>
# 🚀 ProcPilot - Lightweight Terminal Process Intelligence Manager

## 🎉 Introduction

**ProcPilot** is a zero-dependency, cross-platform terminal process intelligence management tool designed for developers and system administrators. It provides powerful features including real-time process monitoring, resource analysis, process tree visualization, and intelligent alerts to help you easily control system process states.

### 💡 Inspiration

In daily development and operations work, we often need to monitor system processes and troubleshoot resource usage issues. Existing tools are either too complex or rely heavily on third-party libraries. ProcPilot was born to provide a **lightweight, efficient, zero-dependency** process management experience.

### ✨ Core Features

- 🔍 **Real-time Process Monitoring** - Track CPU and memory usage in real-time
- 🌳 **Process Tree Visualization** - Intuitively display parent-child relationships
- 🚨 **Intelligent Alert System** - Automatically detect and alert on resource anomalies
- 🏷️ **Tags & Groups** - Flexibly organize and manage processes
- 📊 **Resource Analysis Reports** - One-click export of detailed reports
- 💻 **Beautiful TUI Interface** - Terminal interactive operation interface
- ⚡ **Zero Dependencies** - Pure Python standard library implementation
- 🌍 **Cross-Platform Support** - Linux / macOS / Windows

---

## 🚀 Quick Start

### Requirements

- Python 3.8 or higher
- Supports Linux, macOS, Windows

### Installation

```bash
# Install from PyPI
pip install procpilot

# Or install from source
git clone https://github.com/gitstq/procpilot.git
cd procpilot
pip install -e .
```

### Basic Usage

```bash
# Start interactive TUI interface
procpilot

# List all processes
procpilot list

# Show top 10 processes by CPU
procpilot top -n 10

# Display process tree
procpilot tree

# Search processes
procpilot search python

# View process details
procpilot info 1234

# Kill process
procpilot kill 1234

# Export report
procpilot export report.json
```

---

## 📖 Detailed Usage Guide

### Interactive TUI Interface

Run `procpilot` command to start the interactive interface:

| Key | Function |
|-----|----------|
| `↑/↓` | Navigate up/down |
| `PgUp/PgDn` | Page up/down |
| `k` | Kill selected process (SIGTERM) |
| `K` | Force kill (SIGKILL) |
| `s` | Suspend process |
| `r` | Resume process |
| `t` | Toggle tree view |
| `/` | Search processes |
| `n` | Cycle sort mode |
| `a` | View alerts |
| `Enter` | View process details |
| `q` | Quit |
| `?` | Show help |

### Command Line Arguments

#### List Processes

```bash
# Basic list
procpilot list

# Sort by memory
procpilot list --sort memory

# Filter processes
procpilot list --filter python

# JSON output
procpilot list --json
```

#### Process Tree

```bash
# Show full process tree
procpilot tree

# Specify root process
procpilot tree --pid 1

# Limit depth
procpilot tree --depth 3

# Compact format
procpilot tree --compact
```

#### Monitor Mode

```bash
# Start monitoring (default 1 second interval)
procpilot monitor

# Specify interval and duration
procpilot monitor --interval 2 --duration 60
```

### Process Tags & Groups

```bash
# Add tag
procpilot tag 1234 web-server

# Remove tag
procpilot tag 1234 web-server --remove

# Set group
procpilot group 1234 production
```

---

## 💡 Design Philosophy

### Technology Choices

- **Zero-dependency Design**: Uses only Python standard library for maximum compatibility
- **Cross-platform Implementation**: Optimized for Linux (/proc), macOS (ps command), Windows (wmic)
- **Modular Architecture**: Core, monitor, tree, and alert modules are independent and easy to extend

### Architecture

```
procpilot/
├── core.py      # Process management core
├── monitor.py   # Real-time monitoring
├── tree.py      # Process tree visualization
├── alerts.py    # Intelligent alerts
├── tui.py       # Terminal interface
└── cli.py       # Command line entry
```

### Future Roadmap

- [ ] Network connection monitoring support
- [ ] Process performance charts
- [ ] Remote host monitoring support
- [ ] Web interface support
- [ ] Plugin system

---

## 📦 Packaging & Deployment

### Build Distribution Package

```bash
# Install build tools
pip install build

# Build
python -m build

# Generated packages in dist/ directory
```

### Package as Executable

```bash
# Using PyInstaller
pip install pyinstaller
pyinstaller --onefile procpilot/cli.py --name procpilot
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to submit code, report issues, or suggest features!

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

### Commit Convention

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation update
- `refactor`: Code refactoring
- `test`: Test related

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a>
</p>
