from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os
import re
import glob
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
duke_dir = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
sys.path.append(duke_dir)
# 按包导入
from analysis import daily_analysis, weekly_analysis

# 创建路由
router = APIRouter()

class DailyReportResponse(BaseModel):
    date: str
    report_content: str
    focus_count: int
    distraction_count: int
    distraction_ratio: float
    distraction_reasons: Dict[str, int]
    time_analysis: Dict[str, Any]

class WeeklyReportResponse(BaseModel):
    start_date: str
    end_date: str
    report_content: str

class AnalysisStatusResponse(BaseModel):
    success: bool
    message: str
    report_path: Optional[str] = None

# 后台任务：运行日报分析
def run_daily_analysis_task(date: str = None):
    daily_analysis.start_stop_daily_analysis(start=True, date_str=date)

@router.post("/start_daily_analysis", response_model=AnalysisStatusResponse)
async def start_daily_analysis(background_tasks: BackgroundTasks, date: str = None):
    """启动日报分析"""
    try:
        # 验证是否已经在运行
        if daily_analysis.analysis_running:
            return {"success": False, "message": "日报分析已经在运行中"}
        
        # 在后台启动分析任务
        background_tasks.add_task(run_daily_analysis_task, date)
        
        return {"success": True, "message": "日报分析任务已启动", "report_path": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动日报分析失败: {str(e)}")

@router.post("/stop_daily_analysis", response_model=AnalysisStatusResponse)
async def stop_daily_analysis():
    """停止日报分析"""
    try:
        result = daily_analysis.start_stop_daily_analysis(start=False)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止日报分析失败: {str(e)}")

@router.get("/analysis_status")
async def get_analysis_status():
    """获取日报分析状态"""
    return {"is_running": daily_analysis.analysis_running}

@router.get("/available_dates")
async def get_available_dates():
    """获取可用的日期列表（有日志记录的日期）"""
    try:
        # 获取日志文件中的所有日期
        dates = daily_analysis.get_dates_from_log()
        
        # 获取已生成的日报文件日期
        report_dir = "../FocusReports/daily_report"
        report_files = []
        
        if os.path.exists(report_dir):
            report_files = glob.glob(os.path.join(report_dir, "FocusReport_*.txt"))
        
        # 从文件名提取日期
        report_dates = []
        for file in report_files:
            match = re.search(r"FocusReport_(\d{4}-\d{2}-\d{2})\.txt", os.path.basename(file))
            if match:
                report_dates.append(match.group(1))
        
        return {
            "log_dates": dates,
            "report_dates": report_dates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日期列表失败: {str(e)}")

@router.get("/daily_report", response_model=DailyReportResponse)
async def get_daily_report(date: str = Query(None, description="日期格式 YYYY-MM-DD")):
    """获取指定日期的日报分析"""
    try:
        # 如果未指定日期，使用今天的日期
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        # 检查日期格式
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
        
        # 检查报告文件是否已存在
        report_path = f"../FocusReports/daily_report/FocusReport_{date}.txt"
        if os.path.exists(report_path):
            # 读取已存在的报告
            with open(report_path, "r", encoding="utf-8") as f:
                report_content = f.read()
                
            # 解析报告内容，提取重要信息
            focus_count_match = re.search(r"Number of focus records:\s*(\d+)", report_content)
            distraction_count_match = re.search(r"Number of distraction records:\s*(\d+)", report_content)
            distraction_ratio_match = re.search(r"Distraction ratio:\s*([\d.]+)%", report_content)
            
            focus_count = int(focus_count_match.group(1)) if focus_count_match else 0
            distraction_count = int(distraction_count_match.group(1)) if distraction_count_match else 0
            distraction_ratio = float(distraction_ratio_match.group(1))/100 if distraction_ratio_match else 0
            
            # 提取分心原因
            distraction_reasons = {}
            reasons_section = re.search(r"## Distraction Reason Analysis\s*\n(.*?)(?:\n##|\Z)", report_content, re.DOTALL)
            if reasons_section:
                reasons_text = reasons_section.group(1)
                reason_matches = re.findall(r"- (.*?) \(Occurred (\d+) times\)", reasons_text)
                for reason, count in reason_matches:
                    distraction_reasons[reason] = int(count)
            
            # 提取时段分析
            time_analysis = {
                "high_focus_periods": "",
                "high_distraction_periods": "",
                "high_focus_hours": "",
                "high_distraction_hours": ""
            }
            
            time_section = re.search(r"## Time Period Analysis\s*\n(.*?)(?:\n##|\Z)", report_content, re.DOTALL)
            if time_section:
                time_text = time_section.group(1)
                
                for key in time_analysis:
                    pattern = fr"{key.replace('_', ' ').title()}:\s*(.*?)(?:\n|$)"
                    match = re.search(pattern, time_text, re.IGNORECASE)
                    if match:
                        time_analysis[key] = match.group(1).strip()
            
            return {
                "date": date,
                "report_content": report_content,
                "focus_count": focus_count,
                "distraction_count": distraction_count,
                "distraction_ratio": distraction_ratio,
                "distraction_reasons": distraction_reasons,
                "time_analysis": time_analysis
            }
        else:
            # 报告不存在，生成新报告
            # 这将运行分析并生成报告文件
            daily_analysis.analyze_daily_focus(date)
            
            # 递归调用以返回新生成的报告
            return await get_daily_report(date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日报分析失败: {str(e)}")

@router.get("/available_weeks")
async def get_available_weeks():
    """获取可用的周报列表"""
    try:
        weekly_reports = []
        report_dir = "../FocusReports/weekly_report"
        
        if os.path.exists(report_dir):
            report_files = glob.glob(os.path.join(report_dir, "WeeklyReport_*.md"))
            
            for file in report_files:
                match = re.search(r"WeeklyReport_(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})\.md", os.path.basename(file))
                if match:
                    start_date = match.group(1)
                    end_date = match.group(2)
                    weekly_reports.append({
                        "start_date": start_date,
                        "end_date": end_date,
                        "file_path": file
                    })
        
        return {"weekly_reports": weekly_reports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取周报列表失败: {str(e)}")

@router.get("/weekly_report", response_model=WeeklyReportResponse)
async def get_weekly_report(weeks_ago: int = Query(0, description="几周前（0表示本周）")):
    """获取指定周的周报分析"""
    try:
        # 获取指定周的日期范围
        start_date, end_date = weekly_analysis.get_week_range(weeks_ago)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # 检查报告文件是否已存在
        report_path = f"../FocusReports/weekly_report/WeeklyReport_{start_date_str}_to_{end_date_str}.md"
        
        if os.path.exists(report_path):
            # 读取已存在的报告
            with open(report_path, "r", encoding="utf-8") as f:
                report_content = f.read()
        else:
            # 报告不存在，生成新报告
            files, _, _ = weekly_analysis.get_weekly_files(weeks_ago)
            
            if not files:
                return {
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "report_content": f"没有找到 {start_date_str} 到 {end_date_str} 期间的日报文件，无法生成周报。"
                }
            
            # 生成提示词
            prompt = weekly_analysis.get_prompt(files)
            
            # 分析并生成报告
            analysis = weekly_analysis.analyze_prompt_with_ollama(prompt)
            
            # 保存报告
            report_path = weekly_analysis.save_to_weekly_log(analysis, start_date, end_date)
            
            # 读取新生成的报告
            with open(report_path, "r", encoding="utf-8") as f:
                report_content = f.read()
        
        return {
            "start_date": start_date_str,
            "end_date": end_date_str,
            "report_content": report_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取周报分析失败: {str(e)}")

# 后台任务：运行周报分析
def run_weekly_analysis_task(weeks_ago: int = 0):
    weekly_analysis.start_stop_weekly_analysis(start=True, weeks_ago=weeks_ago)

@router.post("/start_weekly_analysis", response_model=AnalysisStatusResponse)
async def start_weekly_analysis(background_tasks: BackgroundTasks, weeks_ago: int = 0):
    """启动周报分析"""
    try:
        # 验证是否已经在运行
        if weekly_analysis.analysis_running:
            return {"success": False, "message": "周报分析已经在运行中"}
        
        # 在后台启动分析任务
        background_tasks.add_task(run_weekly_analysis_task, weeks_ago)
        
        return {"success": True, "message": "周报分析任务已启动", "report_path": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动周报分析失败: {str(e)}")

@router.post("/stop_weekly_analysis", response_model=AnalysisStatusResponse)
async def stop_weekly_analysis():
    """停止周报分析"""
    try:
        result = weekly_analysis.start_stop_weekly_analysis(start=False)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止周报分析失败: {str(e)}")

@router.get("/weekly_analysis_status")
async def get_weekly_analysis_status():
    """获取周报分析状态"""
    return {"is_running": weekly_analysis.analysis_running} 