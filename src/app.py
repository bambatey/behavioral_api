from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes import admin_routes, auth_routes, session_routes


app = FastAPI(
    title="Behavioral Tests API",
    description="Latin-square context+sentence judgment test backend (Firestore).",
    version="2.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(session_routes.router)
app.include_router(admin_routes.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8001,
        log_level="info",
        reload=True,
    )
