from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routers import monitor, fatigue, analysis_api

app = FastAPI(title="DuKe Focus Monitoring System")

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境中应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(monitor.router, prefix="/api/monitor", tags=["监控"])
app.include_router(fatigue.router, prefix="/api/fatigue", tags=["疲劳度"])
app.include_router(analysis_api.router, prefix="/api/analysis", tags=["数据分析"])

@app.get("/")
async def root():
    return {"message": "DuKe Focus Monitoring System API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 