"""
安全工具函数

提供安全相关的工具函数，如随机字符串生成、密钥哈希等。
"""

import base64
import hashlib
import hmac
import os
import secrets
import string
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

import bcrypt
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# 常量定义
API_KEY_PREFIX_LENGTH = 8
API_KEY_SECRET_LENGTH = 32
API_KEY_DELIMITER = "."
KEY_HASH_ITERATIONS = 100000


def generate_random_string(length: int, alphabet: str = None) -> str:
    """
    生成指定长度的随机字符串
    
    Args:
        length: 字符串长度
        alphabet: 字符集，默认为字母和数字
        
    Returns:
        随机字符串
    """
    if alphabet is None:
        alphabet = string.ascii_letters + string.digits
        
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_api_key() -> Tuple[str, str]:
    """
    生成API密钥
    
    Returns:
        (prefix, secret) 元组
    """
    prefix = generate_random_string(API_KEY_PREFIX_LENGTH)
    secret = generate_random_string(API_KEY_SECRET_LENGTH)
    
    return prefix, secret


def format_api_key(prefix: str, secret: str) -> str:
    """
    格式化API密钥
    
    Args:
        prefix: 密钥前缀
        secret: 密钥主体
        
    Returns:
        完整的API密钥
    """
    return f"{prefix}{API_KEY_DELIMITER}{secret}"


def split_api_key(api_key: str) -> Tuple[str, str]:
    """
    分割API密钥
    
    Args:
        api_key: 完整的API密钥
        
    Returns:
        (prefix, secret) 元组
        
    Raises:
        ValueError: 如果密钥格式无效
    """
    parts = api_key.split(API_KEY_DELIMITER, 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError("无效的API密钥格式")
    
    return parts[0], parts[1]


def hash_secret(secret: str) -> str:
    """
    对密钥主体进行安全哈希
    
    Args:
        secret: 密钥主体
        
    Returns:
        哈希后的密钥
    """
    # 使用bcrypt进行哈希，自动包含盐值
    return bcrypt.hashpw(secret.encode(), bcrypt.gensalt()).decode()


def verify_secret(secret: str, secret_hash: str) -> bool:
    """
    验证密钥主体是否与哈希匹配
    
    Args:
        secret: 密钥主体
        secret_hash: 存储的哈希值
        
    Returns:
        是否匹配
    """
    return bcrypt.checkpw(secret.encode(), secret_hash.encode())


def generate_hmac_signature(data: str, secret: str) -> str:
    """
    生成HMAC签名
    
    Args:
        data: 要签名的数据
        secret: 签名密钥
        
    Returns:
        Base64编码的签名
    """
    signature = hmac.new(
        secret.encode(),
        data.encode(),
        hashlib.sha256
    ).digest()
    
    return base64.b64encode(signature).decode()


def verify_hmac_signature(data: str, signature: str, secret: str) -> bool:
    """
    验证HMAC签名
    
    Args:
        data: 已签名的数据
        signature: Base64编码的签名
        secret: 签名密钥
        
    Returns:
        签名是否有效
    """
    try:
        expected = generate_hmac_signature(data, secret)
        return hmac.compare_digest(signature, expected)
    except Exception:
        return False


def derive_key(master_key: str, context: str, length: int = 32) -> bytes:
    """
    从主密钥派生出特定上下文的子密钥
    
    Args:
        master_key: 主密钥
        context: 上下文标识符
        length: 派生密钥长度
        
    Returns:
        派生的密钥
    """
    salt = hashlib.sha256(context.encode()).digest()
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=KEY_HASH_ITERATIONS,
    )
    
    return kdf.derive(master_key.encode())


def is_key_expired(expires_at: Optional[datetime]) -> bool:
    """
    检查密钥是否已过期
    
    Args:
        expires_at: 过期时间，None表示永不过期
        
    Returns:
        是否已过期
    """
    if expires_at is None:
        return False
        
    return expires_at < datetime.now()


def calculate_expiry(days: Optional[int] = None) -> Optional[datetime]:
    """
    计算过期时间
    
    Args:
        days: 有效天数，None表示永不过期
        
    Returns:
        过期时间
    """
    if days is None:
        return None
        
    return datetime.now() + timedelta(days=days) 