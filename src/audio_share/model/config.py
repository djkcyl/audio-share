from typing import Optional
from pydantic import BaseModel


class TencentCosConfig(BaseModel):
    secret_id: str = "secret_id"
    secret_key: str = "secret_key"
    region: str = "ap-shanghai"
    bucket: str = "audio-share"
    domain: Optional[str] = None


class AudioShareConfig(BaseModel):
    allowed_max_size: int = 100 * 1024 * 1024
    share_url_length: int = 6


class Config(BaseModel):
    tencent_cos: TencentCosConfig = TencentCosConfig()
    audio_share: AudioShareConfig = AudioShareConfig()
