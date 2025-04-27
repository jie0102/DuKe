from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
import datetime

# 添加DuKe系统的路径
sys.path.append("../../")
from fatigue_degree import focus_fatigue_calculator

# 创建路由
router = APIRouter()

class FatigueScore(BaseModel):
    score: float
    level: str
    advice: str
    color: str
    intervene: bool
    distraction_count: int
    total_count: int
    distraction_reasons: List[str]

class FatigueReport(BaseModel):
    date: str
    score: float
    report: str

@router.get("/current", response_model=FatigueScore)
async def get_current_fatigue():
    """获取当前疲劳度分数和等级"""
    try:
        # 读取日志
        logs = focus_fatigue_calculator.read_focus_log("../focus_log.txt")
        
        # 过滤今天的日志
        today_logs = focus_fatigue_calculator.filter_today_logs(logs)
        
        # 计算疲劳分数
        fatigue_score, distraction, total = focus_fatigue_calculator.compute_fatigue_score(today_logs)
        
        # 获取疲劳等级和建议
        level, advice, color, intervene = focus_fatigue_calculator.get_fatigue_level_and_advice(fatigue_score)
        
        # 获取主要分心原因
        distraction_reasons = focus_fatigue_calculator.extract_main_distraction_reasons(today_logs)
        
        return {
            "score": fatigue_score,
            "level": level,
            "advice": advice,
            "color": color,
            "intervene": intervene,
            "distraction_count": distraction,
            "total_count": total,
            "distraction_reasons": distraction_reasons
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算疲劳度失败: {str(e)}")

@router.get("/report", response_model=FatigueReport)
async def generate_fatigue_report():
    """生成疲劳度干预报告"""
    try:
        # 获取当前疲劳状态
        fatigue_data = await get_current_fatigue()
        
        # 只有需要干预时才生成报告
        if fatigue_data["intervene"]:
            # 生成干预报告
            report = focus_fatigue_calculator.generate_intervention_report(
                fatigue_data["level"], 
                fatigue_data["score"], 
                fatigue_data["distraction_reasons"]
            )
            
            return {
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "score": fatigue_data["score"],
                "report": report
            }
        else:
            return {
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "score": fatigue_data["score"],
                "report": "当前状态良好，无需干预。"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成疲劳度报告失败: {str(e)}")

@router.get("/historical")
async def get_historical_fatigue(days: int = 7):
    """获取历史疲劳度数据"""
    try:
        # 读取日志
        logs = focus_fatigue_calculator.read_focus_log("../focus_log.txt")
        
        # 按日期分组
        date_groups = {}
        for log in logs:
            date_str = log['timestamp'].strftime("%Y-%m-%d")
            if date_str not in date_groups:
                date_groups[date_str] = []
            date_groups[date_str].append(log)
        
        # 计算每日疲劳度
        results = []
        today = datetime.datetime.now().date()
        
        for i in range(days):
            date = today - datetime.timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            if date_str in date_groups:
                fatigue_score, distraction, total = focus_fatigue_calculator.compute_fatigue_score(date_groups[date_str])
                level, advice, color, _ = focus_fatigue_calculator.get_fatigue_level_and_advice(fatigue_score)
                
                results.append({
                    "date": date_str,
                    "score": fatigue_score,
                    "level": level,
                    "color": color,
                    "distraction_count": distraction,
                    "total_count": total
                })
            else:
                # 没有数据的日期
                results.append({
                    "date": date_str,
                    "score": 0,
                    "level": "无数据",
                    "color": "Gray",
                    "distraction_count": 0,
                    "total_count": 0
                })
        
        return {"historical_data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史疲劳度数据失败: {str(e)}") 