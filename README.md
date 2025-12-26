# 学习通课程 PDF 提取工具 (Chaoxing PDF Extractor)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

这是一个自动化脚本，用于从学习通（Chaoxing）课程页面提取章节内容（PPT、文档图片）并保存为 PDF 文件。

## 📖 项目背景

在许多学习通课程中，教学 PPT 往往被直接嵌入在课程章节页面里，官方并未提供下载按钮。这给离线阅读、资料整理以及后续的 AI 辅助分析带来了不便。

![PPT无法下载](./Figures/example1.png)

**本工具旨在解决这一痛点**：它能自动遍历课程章节，抓取嵌入的 PPT 图片，并将其无损合并为 PDF 文档，让知识触手可及。

## ✨ 功能特点

- **多浏览器支持**：兼容 **Microsoft Edge** (默认) 和 **Google Chrome**。
- **全自动遍历**：只需提供课程首页链接，脚本即可自动解析侧边栏，批量获取所有章节。
- **智能归档**：自动识别课程名称，创建独立文件夹，并按章节顺序命名和归档 PDF。
- **便捷登录**：启动后自动打开浏览器，支持扫码或验证码登录，无需复杂的 Cookie 抓取配置。
- **深度提取**：自动识别并提取页面中的 PPT 及文档图片，智能处理复杂的嵌套 Iframe 结构。
- **详细反馈**：提供清晰的进度日志，包括透明通道图片检测与处理提示。

## 🛠️ 环境要求

- **操作系统**：Windows / Mac / Linux
- **编程语言**：Python 3.8+
- **浏览器**：Microsoft Edge 或 Google Chrome

## 📦 安装步骤

1.  **获取代码**
    克隆仓库或下载压缩包到本地：
    ```bash
    git clone https://github.com/your-username/chaoxing-pdf-extractor.git
    cd chaoxing-pdf-extractor
    ```

2.  **安装依赖**
    在终端中运行以下命令安装所需的 Python 库：
    ```bash
    pip install -r requirements.txt
    ```

3.  **准备驱动 (可选)**
    *   **Chrome 用户**：脚本内置自动驱动管理，通常无需操作。如遇网络问题，请手动下载 `chromedriver.exe` 放入项目根目录。
    *   **Edge 用户**：脚本默认调用系统 Edge。如启动失败，请下载对应的 `msedgedriver.exe` 放入项目根目录。

## 🚀 使用指南

### 第一步：配置目标课程
打开 `main.py` 文件，找到 `TARGET_COURSE_URL` 变量。将其修改为你想要下载的课程页面链接（通常是包含左侧章节列表的页面）。

![课程章节页面](./Figures/Step1.png)

```python
# main.py
TARGET_COURSE_URL = "https://mooc2-ans.chaoxing.com/..." 
```
![修改变量页面](./Figures/Step2.png)

### 第二步：运行脚本
在终端中执行：
```bash
python main.py
```

### 第三步：选择浏览器
脚本启动后会提示选择浏览器，输入数字并回车：
```text
请选择浏览器:
1. Edge (默认)
2. Chrome
```

### 第四步：登录账号
浏览器会自动打开学习通登录页。请手动完成登录（推荐扫码）。
**注意**：登录成功并看到课程章节列表后，请回到终端窗口。

### 第五步：开始下载
在终端窗口按 **回车键 (Enter)**。脚本将自动开始工作，解析章节并下载 PDF 到 `downloads/课程名称/` 目录下。

## ⚠️ 注意事项

*   **防封控机制**：为了安全起见，脚本在页面跳转时设有短暂延时，请耐心等待。
*   **内容支持**：目前主要支持提取**图片格式**的 PPT 和文档。纯视频章节可能会被跳过。
*   **Alpha 通道提示**：控制台若出现 "Image contains an alpha channel" 提示属正常现象，脚本会自动处理并保留原图质量。

## 📝 常见问题

**Q: 报错 `NoSuchWindowException`?**
A: 请勿在脚本运行过程中手动关闭浏览器窗口。

**Q: 报错 `Unable to obtain driver`?**
A: 这通常是网络问题导致驱动下载失败。请尝试手动下载对应的浏览器驱动（Chromedriver 或 EdgeDriver）并放到脚本目录下。

## ⚖️ 免责声明

1.  **仅供学习交流**：本项目仅用于个人学习和技术交流，旨在辅助用户更方便地进行离线学习。
2.  **合法合规使用**：请勿将本工具用于任何商业用途或非法用途。使用本工具时，请遵守相关法律法规及目标网站（学习通/超星）的服务条款。
3.  **数据安全**：本工具不会收集用户的任何账号信息或个人隐私数据。所有操作均在用户本地进行。
4.  **责任限制**：开发者不对因使用本工具而产生的任何直接或间接损失（包括但不限于账号封禁、数据丢失等）承担责任。用户需自行承担使用风险。

## 📄 License

MIT License
