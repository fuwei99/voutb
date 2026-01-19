import boto3
import hashlib
import time
from typing import Optional, Tuple
from botocore.exceptions import ClientError
import config as app_config


class R2Uploader:
    """Cloudflare R2 图片上传工具"""
    
    def __init__(self):
        self.enabled = app_config.R2_ENABLED
        self.client = None
        self.bucket_name = app_config.R2_BUCKET_NAME
        self.public_url = app_config.R2_PUBLIC_URL.rstrip('/')
        
        if self.enabled:
            if not all([
                app_config.R2_ACCOUNT_ID,
                app_config.R2_ACCESS_KEY_ID,
                app_config.R2_SECRET_ACCESS_KEY,
                app_config.R2_BUCKET_NAME,
                app_config.R2_PUBLIC_URL
            ]):
                print("WARNING: R2_ENABLED is true but R2 configuration is incomplete. R2 upload will be disabled.")
                self.enabled = False
            else:
                try:
                    # 初始化 S3 客户端（R2 兼容 S3 API）
                    from botocore.config import Config
                    self.client = boto3.client(
                        's3',
                        endpoint_url=f'https://{app_config.R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
                        aws_access_key_id=app_config.R2_ACCESS_KEY_ID,
                        aws_secret_access_key=app_config.R2_SECRET_ACCESS_KEY,
                        region_name='auto',  # R2 使用 'auto' 作为区域
                        config=Config(proxies={}) # 强制绕过代理
                    )
                    print(f"R2 Uploader initialized successfully. Bucket: {self.bucket_name}")
                except Exception as e:
                    print(f"ERROR: Failed to initialize R2 client: {e}")
                    self.enabled = False
    
    def _generate_filename(self, image_bytes: bytes, mime_type: str) -> str:
        """
        根据图片内容生成唯一文件名
        使用 MD5 哈希 + 时间戳确保唯一性
        """
        # 获取文件扩展名
        ext_map = {
            'image/png': 'png',
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/gif': 'gif',
            'image/webp': 'webp',
            'image/bmp': 'bmp',
            'image/svg+xml': 'svg'
        }
        ext = ext_map.get(mime_type.lower(), 'png')
        
        # 生成内容哈希
        content_hash = hashlib.md5(image_bytes).hexdigest()[:16]
        
        # 添加时间戳确保唯一性
        timestamp = int(time.time() * 1000)
        
        # 生成文件名：images/年月/哈希_时间戳.扩展名
        year_month = time.strftime('%Y%m')
        filename = f"images/{year_month}/{content_hash}_{timestamp}.{ext}"
        
        return filename
    
    def upload_image(self, image_bytes: bytes, mime_type: str) -> Optional[str]:
        """
        上传图片到 R2
        
        Args:
            image_bytes: 图片二进制数据
            mime_type: 图片 MIME 类型
            
        Returns:
            成功返回图片 URL，失败返回 None
        """
        if not self.enabled:
            return None
        
        try:
            filename = self._generate_filename(image_bytes, mime_type)
            
            # 上传到 R2
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=image_bytes,
                ContentType=mime_type,
                CacheControl='public, max-age=31536000',  # 缓存一年
            )
            
            # 生成公开访问 URL
            image_url = f"{self.public_url}/{filename}"
            
            print(f"Image uploaded to R2: {image_url}")
            return image_url
            
        except ClientError as e:
            print(f"ERROR: Failed to upload image to R2: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error during R2 upload: {e}")
            return None
    
    def is_enabled(self) -> bool:
        """检查 R2 上传是否已启用"""
        return self.enabled


# 全局单例
_r2_uploader_instance: Optional[R2Uploader] = None


def get_r2_uploader() -> R2Uploader:
    """获取 R2 上传器单例"""
    global _r2_uploader_instance
    if _r2_uploader_instance is None:
        _r2_uploader_instance = R2Uploader()
    return _r2_uploader_instance