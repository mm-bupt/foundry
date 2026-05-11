import uvicorn
from dream_foundry.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "dream_foundry.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
