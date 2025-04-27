[简体中文](README.CHN.md) | [English](README.md)

# 度刻(DuKe) - 智能专注度监控与分析系统
基于人工智能的实时专注度监控、疲劳评估和数据分析系统，帮助用户提高工作效率。

## 项目简介

度刻(DuKe)是一款致力于帮助用户"把握每一刻，专注付出"的智能系统。它通过实时监控用户的屏幕内容和应用程序，结合大语言模型智能判断用户的专注状态，计算疲劳度并在必要时进行干预提醒。系统还提供全面的数据分析功能，生成日报和周报，帮助用户了解自己的专注模式并不断改进。

特别关注现代工作环境中用户的心理健康与认知负荷，度刻(DuKe)基于认知资源耗竭模型，科学评估疲劳程度，及时提供个性化干预建议。通过智能分析分心模式和原因，帮助用户识别潜在压力源，调整工作节奏，实现工作与休息的平衡。系统不仅提高工作效率，更致力于缓解心理疲劳，减轻焦虑，为用户创造更健康、可持续的工作状态。

## 使用教程

如果你是第一次使用本系统，以下是详细的入门指南：

### 环境准备

1. **安装Python**：
   - 访问 [Python官网](https://www.python.org/downloads/) 下载Python 3.10或更高版本
   - 安装时勾选"Add Python to PATH"选项
   - 完成安装后，打开命令提示符（Win+R，输入cmd），输入`python --version`确认安装成功

2. **安装Node.js 14+**
   - 前往官网下载

2. **安装Tesseract-OCR**：
   - 下载 [Tesseract-OCR安装包](https://github.com/UB-Mannheim/tesseract/wiki)
   - 安装到默认路径（通常是`C:\Program Files\Tesseract-OCR\`）
   - 确保安装中文语言包

3. **下载本项目**：
   - 通过Git: `git clone https://github.com/jie0102/DuKe.git`
   - 或直接从GitHub下载ZIP文件并解压

4. **安装依赖库**：
   - 打开命令提示符，进入项目目录：`cd 路径\到\DuKe目录`
   - 执行：`pip install -r requirements.txt`

### 首次使用
**1.启动后端服务**
```bash

cd Duke-Web/backend
python main.py

```
**2.启动开发服务器**
```bash
# 安装依赖
cd Duke-Web/frontend
npm install

# 启动开发服务器
npm start
```
**3.进入系统**

访问 http://localhost:3000 打开Web界面

使用左侧菜单导航到不同功能模块

### 常见问题

1. **系统无法启动**：
   - 检查Python是否正确安装
   - 确认已安装所有依赖库：`pip install -r requirements.txt`
   - 检查Tesseract-OCR是否正确安装

2. **OCR识别不准确**：
   - 确保Tesseract-OCR中安装了多种语言语言包
   - 调整屏幕亮度和对比度以提高识别率

3. **无法生成报告**：
   - 确保已有足够的监控记录（至少使用几小时）
   - 检查日志文件`focus_log.txt`是否存在并有内容

4. **系统提醒过于频繁**：
   - 调整工作相关应用的白名单设置
   - 更精确地设置可能分散注意力的黑名单应用

## 系统架构

该系统由三个主要模块组成：

### 1. 监控模块 (`monitor/`)

实时监控用户的专注状态，包括：
- 屏幕内容捕获与OCR识别：使用mss和Tesseract-OCR识别屏幕内容
- 运行程序监测：通过win32gui识别当前运行的所有应用程序
- 基于白名单/黑名单的专注状态判断：结合大语言模型分析工作相关性
- 实时记录日志：将专注状态记录到日志文件中
- 干预提醒：当检测到明显分心时弹出提醒窗口
- 截图管理：自动清理过多的截图文件

### 2. 疲劳度计算模块 (`fatigue_degree/`)

基于监控数据计算用户的疲劳程度：
- 读取监控日志数据：解析focus_log.txt中的专注记录
- 分析分心率与模式：计算当天的分心频率和主要分心原因
- 基于认知资源耗竭模型计算疲劳分数：根据分心率评估疲劳等级
- 疲劳等级评估：将疲劳分为良好状态、轻度疲劳、中度疲劳和高度疲劳四个等级
- 生成个性化干预建议：结合分心原因提供针对性的改进建议

### 3. 数据分析模块 (`analysis/`)

分析用户的长期专注状态数据：
- 日报分析：分析单日专注与分心情况，包括基础统计、时间模式分析、分心原因分析等
- 周报分析：汇总一周数据，分析长期专注趋势和模式
- 趋势识别：识别专注和疲劳的长期变化规律
- 时间段分析：确定一天中专注度最高和最低的时间段
- 个性化建议：结合用户的工作习惯提供改进建议

### 4. Web应用界面 (`DuKe-Web/`)

提供可视化界面和管理功能：
- 前端：展示专注度和疲劳度数据可视化图表
- 后端：提供API接口，处理前端请求
- 报告管理：查看和管理历史日报和周报


## 技术实现

- **大语言模型集成**：使用Qwen2.5:7b等模型进行智能判断，通过远程API访问
- **认知资源耗竭模型**：基于专业心理学理论计算疲劳度，从四个等级评估用户状态
- **OCR技术**：使用Tesseract-OCR识别屏幕内容，评估工作相关性
- **进程监控**：使用win32gui检测后台运行应用，结合白名单/黑名单判断专注状态
- **数据分析算法**：分析用户专注模式和分心原因，识别长期趋势
- **生成式AI应用**：利用大模型生成个性化分析报告和改进建议

## 贡献

欢迎提交问题和改进建议！

## 许可

本项目采用 MIT License 开源协议，欢迎学习、修改与二次开发。


## Star History

<a href="https://www.star-history.com/#jie0102/DuKe&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=jie0102/DuKe&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=jie0102/DuKe&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=jie0102/DuKe&type=Date" />
 </picture>
</a>