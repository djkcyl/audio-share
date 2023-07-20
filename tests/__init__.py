import asyncio

from audio_share.curd import init_db, generate_short_url, get_object_by_su
from audio_share.config import config


async def test_su():
    await init_db()
    obj = await get_object_by_su("test")
    if obj:
        print(obj.dict())
    else:
        print("not found")


async def test_generate_su():
    await init_db()
    short_url = await generate_short_url()
    print(short_url)


if __name__ == "__main__":
    asyncio.run(test_generate_su())
