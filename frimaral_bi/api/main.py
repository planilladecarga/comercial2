"""
FRIMARAL BI - Centro de Comando Comercial + Business Query Engine + Commercial Intelligence
FastAPI Server - Sprint 6 + Sprint 7 + Sprint 8
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.comando import router as comando_router
from .routes.business_query import router as query_router
from .routes.commercial_intelligence import router as ci_router
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
app.include_router(ci_router, prefix="/api/v1/commercial-intelligence", tags=["Commercial Intelligence"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "FRIMARAL BI Centro de Comando"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
