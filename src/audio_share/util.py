import json
import socket
import struct
import hashlib
import subprocess

from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

from .cos import upload_to_cos

Path("tmp").mkdir(exist_ok=True, parents=True)


def get_expire_time(expire_time: int):
    return datetime.now(tz=ZoneInfo("Asia/Shanghai")) + timedelta(days=expire_time)


def ip_to_int(ip: Optional[str]):
    if not ip:
        return 0
    packed_ip = socket.inet_aton(ip)
    return struct.unpack("!I", packed_ip)[0]


def int_to_ip(int):
    if int == 0:
        return None
    unpacked_ip = struct.pack("!I", int)
    return socket.inet_ntoa(unpacked_ip)


def get_md5(file: bytes | str):
    if isinstance(file, str):
        file = file.encode("utf-8")
    return hashlib.md5(file).hexdigest()


class AudioInfo:
    def __init__(self, file: bytes | Path):
        if isinstance(file, bytes):
            self.file_id = get_md5(file)
            tmp = Path("tmp").joinpath(self.file_id)
            tmp.write_bytes(file)
            self.file = tmp
        elif isinstance(file, Path):
            self.file_id = get_md5(file.read_bytes())
            self.file = file
        else:
            raise TypeError("file must be bytes or Path object")
        self.ffmpeg_info = self.get_audio_info()
        self.audio_format: str = self.ffmpeg_info["format"]["format_name"]

    def get_audio_info(self):
        args = ["ffprobe", "-show_format", "-show_streams", "-of", "json", self.file.as_posix()]
        out = self.ffmpeg_cmd(args, "ffprobe")
        return json.loads(out.decode("utf-8"))

    @property
    def audio_sample_rate(self):
        return int(self.ffmpeg_info["streams"][0]["sample_rate"])

    def convert_to_opus(self, voip: bool = True):
        out_file: Path = self.file.parent.joinpath(f"{self.file.stem}.opus")

        args = ["ffmpeg", "-i", self.file.as_posix(), "-c:a", "libopus"]
        if voip:
            args += ["-b:a", "128k", "-ac", "1", "-application", "voip"]
        else:
            args += ["-b:a", "320k"]

        args += ["-vn", "-f", "opus", out_file.as_posix()]
        self.ffmpeg_cmd(args, "ffmpeg")
        return out_file

    def convert_to_flac(self):
        out_file: Path = self.file.parent.joinpath(f"{self.file.stem}.flac")
        args = [
            "ffmpeg",
            "-i",
            self.file.as_posix(),
            "-c:a",
            "flac",
            "-sample_fmt",
            "s16",
            "-ar",
            "44100",
            out_file.as_posix(),
        ]
        self.ffmpeg_cmd(args, "ffmpeg")
        self.audio_format = "flac"
        return out_file

    def ffmpeg_cmd(self, args, arg1):
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result, err = p.communicate()
        if p.returncode != 0:
            raise Exception(arg1, result, err)
        return result

    def upload_to_cos(self, voip: bool = True):
        if self.audio_format == "wav":
            self.file = self.convert_to_flac()
        opus_file = self.convert_to_opus(voip)
        up_raw = upload_to_cos(self.file.read_bytes(), f"{self.file_id}.{self.audio_format}")
        up_opus = upload_to_cos(opus_file.read_bytes(), f"{self.file_id}.opus")
        return up_raw, up_opus


if __name__ == "__main__":
    ip = "225.148.44.122"
    # int_ip = ip_to_int(ip)
    # print(int_ip)
    # print(int_to_ip(int_ip))
