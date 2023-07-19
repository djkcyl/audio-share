from beanie import init_beanie
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from ..model.db import ShareAudio


async def init_db():
    database_uri = "mongodb://localhost:27017"
    client = AsyncIOMotorClient(database_uri)["audio_share"]
    await init_beanie(database=client, document_models=[ShareAudio])  # type: ignore


async def get_object(short_url: str):
    try:
        return await ShareAudio.find_one(ShareAudio.short_url == short_url)
    except Exception:
        raise HTTPException(status_code=404, detail="Not Found")
