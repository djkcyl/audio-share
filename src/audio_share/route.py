import asyncio

from pathlib import Path
from typing import Optional
from starlette import status
from logging import getLogger
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, Request
from fastapi.responses import RedirectResponse, ORJSONResponse

from .model.db import ShareAudio
from .cos import get_presigned_download_url
from .model.response import ShareAudioResponse
from .util import AudioInfo, get_expire_time, ip_to_int, get_md5
from .curd import (
    get_object_by_su,
    generate_short_url,
    create_object,
    get_object_by_md5,
    get_project_by_md5,
    create_project,
    get_project_by_id,
)

ALLOWED_TYPES = {
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/ogg": "ogg",
    "audio/flac": "flac",
    "audio/mp4": "m4a",
    "audio/aac": "aac",
    "audio/opus": "opus",
}
logger = getLogger(__name__)
router = APIRouter(prefix="/audio_share", tags=["音频分享"])


@router.get("/{short_url}")
async def get_audio(short_url: str):
    obj = await get_object_by_su(short_url)
    if not obj:
        return ORJSONResponse(
            ShareAudioResponse(code=status.HTTP_404_NOT_FOUND, msg="not found").dict(),
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if obj.is_expired():
        return ORJSONResponse(
            ShareAudioResponse(code=status.HTTP_410_GONE, msg="audio expired").dict(), status_code=status.HTTP_410_GONE
        )
    return ShareAudioResponse(code=0, msg="success", data=obj.to_audio_data())


@router.put("/audio")
async def upload_audio(
    request: Request,
    svs_project: Optional[int] = None,
    expire_time: int = 3,
    file_name: Optional[str] = None,
    voip: bool = True,
    file: UploadFile = File(...),
):
    if (file.size or 0) > 1024 * 1024 * 100:
        return ORJSONResponse(
            ShareAudioResponse(code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, msg="file too large").dict(),
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )
    if expire_time > 7:
        return ORJSONResponse(
            ShareAudioResponse(code=status.HTTP_400_BAD_REQUEST, msg="expire time too long").dict(),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not file_name:
        time_str = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"{time_str}_{file.filename}"

    audio = await file.read()
    audio_md5 = get_md5(audio)
    if obj := await get_object_by_md5(audio_md5):
        return ORJSONResponse(
            ShareAudioResponse(code=status.HTTP_409_CONFLICT, msg="conflict", data=obj.to_audio_data()).dict(),
            status_code=status.HTTP_409_CONFLICT,
        )
    short_url = await generate_short_url()
    audio_info = AudioInfo(audio)

    if audio_info.audio_format not in ALLOWED_TYPES.values():
        return ORJSONResponse(
            ShareAudioResponse(
                code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                msg=f"unsupported {audio_info.audio_format}, must be {''.join(ALLOWED_TYPES.values())}",
            ).dict(),
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    await asyncio.to_thread(audio_info.upload_to_cos, voip=voip)

    obj = await create_object(
        ShareAudio(
            upload_ip=ip_to_int(request.client.host if request.client else None),
            file_name=file_name,
            file_id=audio_info.file_id,
            audio_type=audio_info.audio_format,
            audio_sample_rate=audio_info.audio_sample_rate,
            project_id=svs_project,
            short_url=short_url,
            expire_time=get_expire_time(expire_time),
        )
    )
    logger.info(f"create object {obj.id}")
    return ShareAudioResponse(code=0, msg="success", data=obj.to_audio_data())


@router.put("/project")
async def upload_project(svs_project: UploadFile = File(...)):
    if (svs_project.size or 0) > 1024 * 1024 * 10:
        return ORJSONResponse(
            ShareAudioResponse(code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, msg="file too large").dict(),
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )
    if not svs_project.filename:
        return ORJSONResponse(
            ShareAudioResponse(code=status.HTTP_400_BAD_REQUEST, msg="file name is required").dict(),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    file_suffix = Path(svs_project.filename).suffix
    if file_suffix not in [".ds", ".ustx", ".svp"]:
        return ORJSONResponse(
            ShareAudioResponse(
                code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, msg=f"unsupported {file_suffix}, must be ds, ustx or svp"
            ).dict(),
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )
    svs_project_data = svs_project.file.read()
    project_md5 = get_md5(svs_project_data)
    if obj := await get_project_by_md5(project_md5):
        return ORJSONResponse(
            ShareAudioResponse(code=status.HTTP_409_CONFLICT, msg="conflict", data=obj.to_project_data()).dict(),
            status_code=status.HTTP_409_CONFLICT,
        )
    obj = await create_project(svs_project_data, Path(svs_project.filename).suffix)
    return ShareAudioResponse(code=0, msg="success", data=obj.to_project_data())


@router.get("/download/{short_url}")
async def download_audio(short_url: str):
    obj = await get_object_by_su(short_url)
    if not obj:
        return ORJSONResponse(
            ShareAudioResponse(code=status.HTTP_404_NOT_FOUND, msg="not found").dict(),
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if obj.is_expired():
        return ORJSONResponse(
            ShareAudioResponse(code=status.HTTP_410_GONE, msg="audio expired").dict(), status_code=status.HTTP_410_GONE
        )
    download_url = get_presigned_download_url(f"{obj.file_id}.{obj.audio_type}")
    obj.download_count += 1
    await obj.save()  # type: ignore
    return RedirectResponse(url=download_url)


@router.get("/project/{project_id}")
async def get_project(project_id: int):
    if not (project := await get_project_by_id(project_id)):
        return ORJSONResponse(
            ShareAudioResponse(code=status.HTTP_404_NOT_FOUND, msg="not found").dict(),
            status_code=status.HTTP_404_NOT_FOUND,
        )
    project_file = f"{project.project_id}{project.project_suffix}"
    project_url = get_presigned_download_url(project_file)
    return RedirectResponse(url=project_url)
