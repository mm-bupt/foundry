import uvicorn
from foundry_app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "foundry_app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
