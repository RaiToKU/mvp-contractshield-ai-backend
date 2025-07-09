from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import json
import time
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 详细请求日志中间件
class DetailedLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 记录请求信息
        logger.info(f"🔵 REQUEST: {request.method} {request.url}")
        logger.info(f"📋 Headers: {dict(request.headers)}")
        
        # 读取请求体
        body = b""
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if body:
                try:
                    body_str = body.decode('utf-8')
                    logger.info(f"📝 Request Body: {body_str}")
                except:
                    logger.info(f"📝 Request Body (bytes): {body}")
        
        # 重新构造请求以便后续处理
        async def receive():
            return {"type": "http.request", "body": body}
        
        request._receive = receive
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录响应信息
        logger.info(f"🔴 RESPONSE: {response.status_code} - {process_time:.4f}s")
        logger.info(f"📋 Response Headers: {dict(response.headers)}")
        
        # 如果是错误响应，记录更详细信息
        if response.status_code >= 400:
            logger.error(f"❌ ERROR RESPONSE: Status {response.status_code}")
            
            # 尝试读取响应体
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            if response_body:
                try:
                    response_str = response_body.decode('utf-8')
                    logger.error(f"📝 Error Response Body: {response_str}")
                except:
                    logger.error(f"📝 Error Response Body (bytes): {response_body}")
            
            # 重新构造响应
            from fastapi.responses import Response as FastAPIResponse
            return FastAPIResponse(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
        
        return response

# 导入路由
from .routes import upload, review, export, websocket
from .database import init_db

# 创建FastAPI应用
app = FastAPI(
    title="ContractShield AI Backend",
    description="合同审查AI后端服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加详细日志中间件
app.add_middleware(DetailedLoggingMiddleware)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(upload.router)
app.include_router(review.router)
app.include_router(export.router)
app.include_router(websocket.router)

# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "内部服务器错误",
            "status_code": 500
        }
    )

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("Starting ContractShield AI Backend...")
    
    # 初始化数据库
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # 创建必要的目录
    directories = [
        os.getenv("UPLOAD_DIR", "./uploads"),
        "./exports",
        "./logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Directory ensured: {directory}")
    
    logger.info("ContractShield AI Backend started successfully")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("Shutting down ContractShield AI Backend...")
    # 这里可以添加清理逻辑
    logger.info("ContractShield AI Backend shut down successfully")

# 根路径
@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "name": "ContractShield AI Backend",
        "version": "1.0.0",
        "description": "合同审查AI后端服务",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "api": "/api/v1"
        }
    }

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        # 检查数据库连接
        from .database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "service": "ContractShield AI Backend",
            "version": "1.0.0",
            "timestamp": str(int(time.time() * 1000))
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "service": "ContractShield AI Backend",
                "error": str(e),
                "timestamp": str(int(time.time() * 1000))
            }
        )

# API信息
@app.get("/api/v1")
async def api_info():
    """API版本信息"""
    return {
        "version": "v1",
        "endpoints": {
            "upload": "/api/v1/upload",
            "draft_roles": "/api/v1/draft_roles",
            "confirm_roles": "/api/v1/confirm_roles",
            "review": "/api/v1/review",
            "export": "/api/v1/export/{task_id}",
            "websocket": "/ws/review/{task_id}"
        },
        "supported_formats": {
            "upload": ["pdf", "docx", "doc", "jpg", "jpeg", "png"],
            "export": ["pdf", "docx", "txt"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )