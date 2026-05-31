from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router


app = FastAPI(
    title="Face Recognition API",
    description=(
        "A simple and clean REST API built with FastAPI and DeepFace for "
        "face verification."
    ),
    version="1.0.0",
)

# Allow frontend or API clients from different origins to call this service.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", tags=["Health"])
async def health_check() -> dict:
    """Basic health check endpoint."""
    return {"message": "Face Recognition API is running"}
