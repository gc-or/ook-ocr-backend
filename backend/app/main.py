"""
校园二手书 AI 识别 - 后端主入口
FastAPI 应用配置与启动
"""
from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件中的环境变量

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 导入 API 路由
from .api.books import router as books_router

# 创建 FastAPI 应用实例
app = FastAPI(
    title="校园二手书 AI 识别 API",
    description="基于 PaddleOCR + LLM 的书籍信息识别服务",
    version="1.0.0"
)

# 配置 CORS (跨域资源共享)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(books_router)

# 静态文件目录（前端文件）
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"


@app.get("/")
async def root():
    """根路由 - 返回前端页面"""
    index_file = FRONTEND_DIR / "test.html"
    if index_file.exists():
        response = FileResponse(index_file)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return {
        "message": "📚 校园二手书 AI 识别服务已启动!",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/connect")
async def connect_page():
    """连接配置页面"""
    connect_file = FRONTEND_DIR / "connect.html"
    if connect_file.exists():
        return FileResponse(connect_file)
    return {"error": "页面不存在"}


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}


# 这是 Python 直接运行时的入口点
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
