from typing import Optional, Literal
from pydantic import BaseModel
from datetime import datetime


class ShareAudioData(BaseModel):
    upload_time: datetime
    file_name: Optional[str]
    file_id: str
    audio_type: Literal["mp3", "wav", "ogg", "flac", "m4a", "aac", "opus"]
    audio_sample_rate: int
    project_id: Optional[int]
    short_url: str
    play_url: str
    expire_time: datetime
    visit_count: int = 0
    download_count: int = 0


class ProjectData(BaseModel):
    project_id: int
    project_md5: str
    project_suffix: str
    project_upload_time: datetime


class ShareAudioResponse(BaseModel):
    code: int
    msg: str
    data: Optional[ShareAudioData | ProjectData] = None
