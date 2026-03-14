from datetime import datetime, timezone
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_routes, results_routes, admin_routes

app = FastAPI(
    title="Behavioral Tests API",
    description="API for language attrition behavioral tests with Firebase backend",
    version="1.0.0",
    contact={
        "name": "API Support Team",
        "email": "support@example.com",
    },
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware - allow frontend at localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(results_routes.router)
app.include_router(admin_routes.router)

if __name__ == "__main__":
    print(f"🚀 Server başlatılıyor...")
    print("📝 Loglar hem console'da hem de app.log dosyasında görünecek")
    print("🔧 Debug: Current working directory:", __import__("os").getcwd())
    print("🔧 Debug: __file__:", __file__)
    print("=" * 50)

    import uvicorn
    
    uvicorn.run(
        "app:app",  # ---! Import string olarak geçir - reload için gerekli
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,
    )
