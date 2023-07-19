import socket
import struct
import ffmpeg


def ip_to_int(ip):
    packed_ip = socket.inet_aton(ip)
    return struct.unpack("!I", packed_ip)[0]


def int_to_ip(int):
    unpacked_ip = struct.pack("!I", int)
    return socket.inet_ntoa(unpacked_ip)


def get_audio_info(file_path):
    probe = ffmpeg.probe(file_path)
    return probe


if __name__ == "__main__":
    # ip = "225.148.44.122"
    # int_ip = ip_to_int(ip)
    # print(int_ip)
    # print(int_to_ip(int_ip))
    print(get_audio_info("A:\BaiduNetdiskDownload\千千阙歌 (Live).flac"))
