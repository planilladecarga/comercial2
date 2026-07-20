"""
FRIMARAL BI - Centro de Comando Comercial + Business Query Engine
FastAPI Server - Sprint 6 + Sprint 7
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.comando import router as comando_router
from .routes.business_query import router as query_router
from .config import HOST, PORT

app = FastAPI(
    title="FRIMARAL BI - API",
    description="Centro de Comando Comercial y Motor de Consultas - FRIMARAL BI",
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
app.include_router(query_router, prefix="/api/query", tags=["Query"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "FRIMARAL BI Centro de Comando"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
