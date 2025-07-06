from fastapi import FastAPI
from app.api.api import api_router

app = FastAPI(
    title="Options Surface Analyzer API",
    description="API for fetching option data, calibrating SVI surfaces, detecting arbitrage, and simulating trades.",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Options Surface Analyzer Backend!"}
