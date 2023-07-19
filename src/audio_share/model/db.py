from beanie import Document
from zoneinfo import ZoneInfo
from datetime import datetime
from pymongo import IndexModel
from typing import Optional, Literal


class ShareAudio(Document):
    upload_time: datetime = datetime.now(tz=ZoneInfo("Asia/Shanghai"))
    upload_ip: int
    file_name: Optional[str]
    file_md5: str
    audio_type: Literal["mp3", "wav", "ogg", "flac", "m4a", "aac", "opus"]
    audio_sample_rate: int
    short_url: str
    expire_time: datetime
    visit_count: int = 0
    download_count: int = 0

    class Settings:
        name = "share_audio"
        indexes = [IndexModel("file_md5", unique=True), IndexModel("short_url", unique=True)]
