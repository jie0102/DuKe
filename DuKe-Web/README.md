# DuKe-Web 专注监控分析系统

DuKe-Web是对DuKe专注监控分析系统的Web界面实现，提供了直观的用户界面来管理和查看专注监控数据。

## 项目结构

```
DuKe-Web/
├── backend/            # FastAPI后端
│   ├── main.py         # 主应用入口
│   ├── routers/        # API路由
│   │   ├── monitor.py  # 监控相关API
│   │   ├── fatigue.py  # 疲劳度相关API
│   │   └── analysis.py # 数据分析相关API
│   └── core/           # 核心服务集成
└── frontend/           # React前端
    ├── public/         # 静态资源
    └── src/            # 源代码
        ├── components/ # 组件
        ├── pages/      # 页面
        └── ...
```

## 功能特性

- **实时监控**: 配置和启动专注监控，查看实时状态
- **疲劳度分析**: 查看当前疲劳度状态，获取干预建议
- **日报分析**: 查看每日专注状态统计和详细报告
- **周报分析**: 查看每周专注趋势和改进建议

## 安装与运行

### 前提条件

- Python 3.8+
- Node.js 14+
- DuKe核心系统

### 后端安装

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端服务
cd backend
python main.py
```

### 前端安装

```bash
# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm start
```

## 使用说明

1. 启动后端和前端服务
2. 访问 http://localhost:3000 打开Web界面
3. 使用左侧菜单导航到不同功能模块

### 监控模块

- 设置工作目标和应用白名单/黑名单
- 启动/停止监控
- 查看最近的监控记录

### 疲劳度模块

- 查看当前疲劳指数和级别
- 生成干预建议报告
- 查看历史疲劳度趋势

### 日报分析

- 选择日期查看详细分析
- 查看专注/分心统计数据
- 分析分心原因和时段分布

### 周报分析

- 选择周数查看周报
- 生成新的周报
- 查看历史周报记录

## 技术栈

- **后端**: FastAPI, Python
- **前端**: React, Ant Design
- **通信**: Axios, RESTful API
- **数据可视化**: Ant Design Charts 