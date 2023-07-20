from qcloud_cos import CosConfig, CosS3Client

from .config import config

cos_config = CosConfig(
    Region=config.tencent_cos.region,
    SecretId=config.tencent_cos.secret_id,
    SecretKey=config.tencent_cos.secret_key,
    Domain=config.tencent_cos.domain,
)

client = CosS3Client(cos_config)
Bucket = config.tencent_cos.bucket


def upload_to_cos(data: bytes, object_name: str):
    return client.put_object(Bucket=Bucket, Body=data, Key=object_name, EnableMD5=False)


def get_presigned_download_url(key):
    return client.get_presigned_download_url(Bucket=Bucket, Key=key, Expired=30)
