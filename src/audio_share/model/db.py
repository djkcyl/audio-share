from typing import Optional
from beanie import Document
from zoneinfo import ZoneInfo
from datetime import datetime
from pymongo import IndexModel

from ..cos import get_presigned_download_url
from .response import ShareAudioData, ProjectData


class ShareAudio(Document):
    upload_time: datetime = datetime.now(tz=ZoneInfo("Asia/Shanghai"))
    upload_ip: int
    file_name: Optional[str]
    file_id: str
    audio_type: str
    audio_sample_rate: int
    project_id: Optional[int]
    short_url: str
    expire_time: datetime
    visit_count: int = 0
    download_count: int = 0

    class Settings:
        name = "share_audio"
        indexes = [IndexModel("file_id", unique=True), IndexModel("short_url", unique=True)]

    def is_expired(self):
        return self.expire_time.replace(tzinfo=ZoneInfo("Asia/Shanghai")) < datetime.now(tz=ZoneInfo("Asia/Shanghai"))

    def to_audio_data(self):
        return ShareAudioData(
            **{
                "upload_time": self.upload_time,
                "file_name": self.file_name,
                "file_id": self.file_id,
                "audio_type": self.audio_type,
                "audio_sample_rate": self.audio_sample_rate,
                "short_url": self.short_url,
                "project_id": self.project_id,
                "play_url": get_presigned_download_url(f"{self.file_id}.opus"),
                "expire_time": self.expire_time,
                "visit_count": self.visit_count,
                "download_count": self.download_count,
            }
        )


class SVSProject(Document):
    project_id: int
    project_md5: str
    project_suffix: str
    project_upload_time: datetime = datetime.now(tz=ZoneInfo("Asia/Shanghai"))

    class Settings:
        name = "svs_project"
        indexes = [IndexModel("project_id", unique=True), IndexModel("project_md5", unique=True)]

    def to_project_data(self):
        return ProjectData(
            **{
                "project_id": self.project_id,
                "project_suffix": self.project_suffix,
                "project_md5": self.project_md5,
                "project_upload_time": self.project_upload_time,
            }
        )
