"""
空岗信息发布对接平台 - FastAPI应用入口
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print(f"[START] {settings.PROJECT_NAME}")
    print(f"[ENV] {settings.ENV}")
    print(f"[DB] {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Not configured'}")
    yield
    # 关闭时执行
    print("[STOP] Application shutdown")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI增强型空岗信息发布对接平台",
    version="1.0.0",
    docs_url="/docs" if settings.ENV != "prod" else None,
    redoc_url="/redoc" if settings.ENV != "prod" else None,
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "空岗信息发布对接平台 API",
        "version": "1.0.0",
        "docs": "/docs" if settings.ENV != "prod" else "disabled in production",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "env": settings.ENV,
    }


# 注册路由
from app.api.v1 import ai_prompts, applications, auth, base_data, company_certifications, jobs, resumes, seeker_profiles, users

app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户"])
app.include_router(company_certifications.router, prefix="/api/v1/company-certifications", tags=["企业认证"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(resumes.router, prefix="/api/v1/resumes", tags=["resumes"])
app.include_router(seeker_profiles.router, prefix="/api/v1/seeker-profiles", tags=["seeker-profiles"])
app.include_router(ai_prompts.router, prefix="/api/v1/ai-prompts", tags=["ai-prompts"])
app.include_router(base_data.router, prefix="/api/v1/base-data", tags=["base-data"])

# TODO: 其他模块路由
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENV == "dev" else False,
    )
