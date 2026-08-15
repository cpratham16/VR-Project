from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter()

@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "unhealthy"
    try:
        # Check DB connection
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        pass
        
    return {
        "status": "online",
        "database": db_status
    }
