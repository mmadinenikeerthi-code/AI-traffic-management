# app/main.py

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

import uvicorn

from app import config, models
from app.database import engine
from app.routers import auth, congestion, dashboard, detect, profile, reports, users

app = FastAPI(
    title=config.APP_NAME,
    version=config.VERSION,
    description="""
AI Powered Traffic Management &
Congestion Detection System

Features
- User Authentication
- Vehicle Detection
- Congestion Detection
- Dashboard
- Reports
- YOLOv8 Integration
- Role Based Access
""",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "frontend", "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(detect.router, prefix="/detect", tags=["AI Detection"])
app.include_router(congestion.router, prefix="/congestion", tags=["Congestion"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])


@app.on_event("startup")
async def startup():
    print("=" * 60)
    print(config.APP_NAME)
    print("System Status :", config.SYSTEM_STATUS)
    print("AI Engine :", config.AI_ENGINE)
    print("Database Connected")
    print("=" * 60)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"title": config.APP_NAME}
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"title": "Login"}
    )


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"title": "Register"}
    )


@app.get("/dashboard-page", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"title": "Dashboard"}
    )


@app.get("/health")
async def health():
    return {
        "status": "Healthy",
        "application": config.APP_NAME,
        "version": config.VERSION,
        "database": "Connected",
        "AI": config.AI_ENGINE,
        "camera": config.CAMERA_STATUS
    }


@app.get("/system")
async def system():
    return {
        "Application": config.APP_NAME,
        "Version": config.VERSION,
        "Status": config.SYSTEM_STATUS,
        "AI Engine": config.AI_ENGINE,
        "Camera": config.CAMERA_STATUS,
        "Debug": config.DEBUG
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": str(exc)
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True
    )
