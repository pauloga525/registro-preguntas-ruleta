from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.auth import router as auth_router
from .routes.preguntas import router as preguntas_router
from .routes.materias import router as materias_router
from .routes.niveles import router as niveles_router

app = FastAPI(title="Login Backend")

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://parish-fred-loves-desirable.trycloudflare.com/",
        "https://parish-fred-loves-desirable.trycloudflare.com",
        "https://end-classified-september-delayed.trycloudflare.com",
        "https://fossil-remarkable-per-challenging.trycloudflare.com",
        "https://occupied-tracking-semester-peaceful.trycloudflare.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ROUTERS
# =========================
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(preguntas_router, prefix="/preguntas", tags=["Preguntas"])
app.include_router(materias_router, prefix="/materias", tags=["Materias"])
app.include_router(niveles_router, prefix="/niveles", tags=["Niveles"])
