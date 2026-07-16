from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import appeals, auth, community, contents, me, reviewer, scenes, topics
from app.core.config import get_settings


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema and demo data are explicit commands so every developer runs the same migration history.
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Context-aware text moderation and human appeal review demo API.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(scenes.router, prefix="/api")
app.include_router(community.router, prefix="/api")
app.include_router(topics.router, prefix="/api")
app.include_router(contents.router, prefix="/api")
app.include_router(me.router, prefix="/api")
app.include_router(appeals.router, prefix="/api")
app.include_router(reviewer.router, prefix="/api")


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok", "service": settings.app_name, "environment": settings.app_env}
