from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from api.database import engine
from api.models import Base
from api.routers import auth, jobs, users
from fastapi.middleware.cors import CORSMiddleware
import httpx


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(users.router)

@app.get("/proxy-image/")
async def proxy_image(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers={
            "Referer": "https://dev.bg/",
            "User-Agent": "Mozilla/5.0"
        })
    return StreamingResponse(
        iter([response.content]),
        media_type=response.headers.get("content-type", "image/png")
    )