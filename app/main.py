from fastapi import FastAPI
from app.routers import taxpayer
from app.routers import invois
from app.core.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bilcekap Backend API",
    description="Backend API for Bilcekap application",
    version="1.0.0"
)

# Include routers
app.include_router(
    taxpayer.router,
    prefix="/api/v1.0/taxpayer",
    tags=["taxpayer"]
)

app.include_router(
    invois.router,
    prefix="/api/v1.0/invois",
    tags=["myinvois"]
)

@app.get("/")
async def root():
    return {"message": "Bilcekap Backend API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
