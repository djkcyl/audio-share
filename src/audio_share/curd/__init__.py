import random
import string
import asyncio

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from ..util import get_md5
from ..config import config
from ..cos import upload_to_cos
from ..model.db import ShareAudio, SVSProject


async def init_db():
    database_uri = "mongodb://localhost:27017"
    client = AsyncIOMotorClient(database_uri)["audio_share"]
    await init_beanie(database=client, document_models=[ShareAudio, SVSProject])  # type: ignore


async def get_object_by_su(short_url: str):
    obj = await ShareAudio.find_one(ShareAudio.short_url == short_url)
    if obj:
        obj.visit_count += 1
        await obj.save()  # type: ignore
        return obj
    return


async def get_object_by_md5(file_id: str):
    return await ShareAudio.find_one(ShareAudio.file_id == file_id)


async def get_project_by_md5(project_md5: str):
    return await SVSProject.find_one(SVSProject.project_md5 == project_md5)


async def get_project_by_id(project_id: int):
    return await SVSProject.find_one(SVSProject.project_id == project_id)


async def generate_short_url():
    short_url = "".join(random.sample(string.ascii_letters + string.digits, config.audio_share.share_url_length))
    if await get_object_by_su(short_url):
        return await generate_short_url()
    return short_url


async def create_object(obj: ShareAudio):
    await obj.insert()  # type: ignore
    if obj.id:
        return obj
    raise RuntimeError("create object failed")


async def create_project(project_data: bytes, project_suffix: str):
    project_md5 = get_md5(project_data)
    if obj := await get_project_by_md5(project_md5):
        return obj
    last_pj = await SVSProject.find_one(sort=[("_id", -1)])
    pjid = last_pj.project_id + 1 if last_pj else 1
    obj = SVSProject(project_id=pjid, project_md5=project_md5, project_suffix=project_suffix)
    project_file = f"{pjid}{project_suffix}"
    await asyncio.to_thread(upload_to_cos, project_data, project_file)
    await obj.insert()  # type: ignore
    if obj.id:
        return obj
    raise RuntimeError("create project failed")
