from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# 添加DuKe系统的路径
sys.path.append("../../")
from monitor import focus_monitor

# 创建路由
router = APIRouter()

# 数据模型
class MonitorSettings(BaseModel):
    work_goal: str
    white_list: List[str]
    black_list: List[str]

class MonitorStatus(BaseModel):
    is_running: bool
    work_goal: Optional[str] = None
    white_list: Optional[List[str]] = None
    black_list: Optional[List[str]] = None

# 全局变量跟踪状态
monitor_status = MonitorStatus(is_running=False)
monitor_task = None

# 后台任务：启动监控
def start_monitoring_task(settings: MonitorSettings):
    global monitor_status
    try:
        # 设置全局变量供focus_monitor使用
        focus_monitor.WHITE_LIST = settings.white_list
        focus_monitor.BLACK_LIST = settings.black_list
        
        # 启动监控
        focus_monitor.run_monitor(
            preset_goal=settings.work_goal,
            preset_white_list=settings.white_list,
            preset_black_list=settings.black_list,
            headless=True  # 无界面模式
        )
    except Exception as e:
        monitor_status.is_running = False
        print(f"监控任务出错: {str(e)}")

@router.post("/start")
async def start_monitoring(settings: MonitorSettings, background_tasks: BackgroundTasks):
    """启动专注监控"""
    global monitor_status, monitor_task
    
    if monitor_status.is_running:
        raise HTTPException(status_code=400, detail="监控已在运行中")
    
    # 更新状态
    monitor_status.is_running = True
    monitor_status.work_goal = settings.work_goal
    monitor_status.white_list = settings.white_list
    monitor_status.black_list = settings.black_list
    
    # 在后台启动监控任务
    background_tasks.add_task(start_monitoring_task, settings)
    
    return {"message": "监控已启动", "status": monitor_status}

@router.post("/stop")
async def stop_monitoring():
    """停止专注监控"""
    global monitor_status
    
    if not monitor_status.is_running:
        raise HTTPException(status_code=400, detail="监控未运行")
    
    # 停止监控
    try:
        # 这里需要一种方式停止focus_monitor
        # 可能需要修改原始代码以支持优雅停止
        # 临时方案：设置一个停止标志
        if hasattr(focus_monitor, "stop_monitoring"):
            focus_monitor.stop_monitoring = True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止监控失败: {str(e)}")
    
    # 更新状态
    monitor_status.is_running = False
    
    return {"message": "监控已停止", "status": monitor_status}

@router.get("/status")
async def get_monitor_status():
    """获取监控状态"""
    global monitor_status
    return monitor_status

@router.get("/recent_logs")
async def get_recent_logs(count: int = 10):
    """获取最近的监控日志"""
    try:
        log_file = "../focus_log.txt"
        if not os.path.exists(log_file):
            return {"logs": []}
        
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 简单解析日志
        log_entries = []
        segments = content.split("-" * 50)
        for segment in segments[-count-1:-1]:  # 获取最近的n条记录
            if segment.strip():
                log_entries.append(segment.strip())
        
        return {"logs": log_entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取日志失败: {str(e)}") 