"""
FRIMARAL BI - Centro de Comando Comercial
FastAPI Server - Sprint 6
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.comando import router as comando_router
from .config import HOST, PORT

app = FastAPI(
    title="FRIMARAL BI - Centro de Comando Comercial",
    description="API para el Dashboard Ejecutivo del Director Comercial",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(comando_router, prefix="/api/comando", tags=["Comando"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "FRIMARAL BI Centro de Comando"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
