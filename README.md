[简体中文](README.CHN.md) | [English](README.md)

# DuKe(度刻) - Intelligent Focus Monitoring & Analysis System

An AI-based real-time focus monitoring, fatigue assessment, and data analysis system, helping users improve their work efficiency.

## Project Introduction

DuKe is an intelligent system dedicated to helping users "make the most of every moment and focus on what matters." It monitors your screen content and running applications in real time, intelligently judges your focus status with large language models, calculates fatigue level, and provides intervention reminders when necessary. The system also provides comprehensive data analysis functions, generating daily and weekly reports to help users understand their own focus patterns and continuously improve.

With special attention to users' mental health and cognitive load in modern work environments, DuKe uses the cognitive resource depletion model to scientifically assess fatigue and provide timely personalized intervention suggestions. Through smart analysis of distraction patterns and reasons, it helps users identify potential stress sources, adjust work rhythm, and achieve a balance between work and rest. The system not only boosts efficiency, but also aims to relieve mental fatigue and anxiety, creating a healthier and more sustainable working state for users.

## Beginner's Guide

If you're using this system for the first time, here's a detailed getting started guide:

### Environment Setup

1. **Install Python**:
   - Visit the [Python website](https://www.python.org/downloads/) to download Python 3.10 or later
   - During installation, check the "Add Python to PATH" option
   - After installation, open the Command Prompt (Win+R, type cmd), and enter `python --version` to confirm successful installation

2. **Install Node.js 14+**:
   - Visit the [Node.js website](https://nodejs.org/) to download Node.js 14 or later
   - Follow the installation instructions

3. **Install Tesseract-OCR**:
   - Download the [Tesseract-OCR installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - Install to the default path (usually `C:\Program Files\Tesseract-OCR\`)
   - Make sure to install multiple language packs

4. **Download this project**:
   - Via Git: `git clone https://github.com/jie0102/DuKe.git`
   - Or download the ZIP file directly from GitHub and extract it

5. **Install dependencies**:
   - Open Command Prompt, navigate to the project directory: `cd path\to\DuKe`
   - Run: `pip install -r requirements.txt`

### First-time Use

**1. Start the backend service**
```bash
cd Duke-Web/backend
python main.py
```

**2. Start the development server**
```bash
# Install dependencies
cd Duke-Web/frontend
npm install

# Start development server
npm start
```

**3. Enter the system**

Visit http://localhost:3000 to open the Web interface

Use the left menu to navigate to different function modules


### Common Issues

1. **System won't start**:
   - Check if Python is installed correctly
   - Confirm all dependencies are installed: `pip install -r requirements.txt`
   - Verify Tesseract-OCR is installed correctly

2. **OCR recognition is inaccurate**:
   - Ensure multiple language packs are installed in Tesseract-OCR
   - Adjust screen brightness and contrast to improve recognition

3. **Cannot generate reports**:
   - Make sure you have sufficient monitoring records (at least a few hours of use)
   - Check if the log file `focus_log.txt` exists and has content

4. **System reminders are too frequent**:
   - Adjust the whitelist settings for work-related applications
   - More precisely define potentially distracting applications in the blacklist

## System Architecture

The system consists of four main modules:

### 1. Monitoring Module (`monitor/`)

Real-time monitoring of user focus status, including:
- Screen content capture and OCR recognition: Using mss and Tesseract-OCR to identify screen content
- Running application monitoring: Using win32gui to detect all currently running applications
- Focus status determination based on whitelist/blacklist: Combined with large language model analysis of work relevance
- Real-time logging: Recording focus status to log files
- Intervention reminders: Pop-up notifications when significant distraction is detected
- Screenshot management: Automatic cleanup of excessive screenshot files

### 2. Fatigue Degree Calculation Module (`fatigue_degree/`)

Calculates user fatigue level based on monitoring data:
- Reading monitoring log data: Parsing focus records from focus_log.txt
- Analyzing distraction rate and patterns: Calculating daily distraction frequency and main distraction causes
- Calculating fatigue score based on cognitive resource depletion model: Assessing fatigue level based on distraction rate
- Fatigue level assessment: Categorizing fatigue into four levels - good focus state, mild fatigue, moderate fatigue, and high fatigue
- Generating personalized intervention suggestions: Providing targeted improvement recommendations based on distraction causes

### 3. Data Analysis Module (`analysis/`)

Analyzes users' long-term focus status data:
- Daily analysis: Analyzing daily focus and distraction status, including basic statistics, time pattern analysis, distraction reason analysis, etc.
- Weekly analysis: Aggregating one week of data to analyze long-term focus trends and patterns
- Trend identification: Identifying long-term patterns of focus and fatigue changes
- Time period analysis: Determining the highest and lowest focus periods throughout the day
- Personalized recommendations: Providing improvement suggestions based on user's work habits

### 4. Web Application Interface (`DuKe-Web/`)

Provides visualization interface and management functions:
- Frontend: Displaying focus and fatigue data visualization charts
- Backend: Providing API endpoints to handle frontend requests
- Report management: Viewing and managing historical daily and weekly reports



## Technical Implementation

- **Large Language Model Integration**: Uses models such as Qwen2.5:7b for intelligent judgment via remote API access
- **Cognitive Resource Depletion Model**: Calculates fatigue degree based on professional psychological theories, assessing user state across four levels
- **OCR Technology**: Uses Tesseract-OCR to recognize screen content to evaluate work relevance
- **Process Monitoring**: Uses win32gui to detect running applications, combined with whitelist/blacklist to determine focus status
- **Data Analysis Algorithms**: Analyzes user focus patterns and distraction causes, identifying long-term trends
- **Generative AI Application**: Leverages large models to generate personalized analysis reports and improvement suggestions

## Contribution

Feedback and suggestions are welcome!

## License

This project is open-sourced under the MIT License. You are welcome to study, modify and further develop it.

## Star History

<a href="https://www.star-history.com/#jie0102/DuKe&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=jie0102/DuKe&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=jie0102/DuKe&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=jie0102/DuKe&type=Date" />
 </picture>
</a>