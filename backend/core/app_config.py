"""统一配置加载器 - 从 .env 和 config.json 加载所有外部配置"""
import json
import os
from dotenv import load_dotenv

# 加载 .env 文件（backend/.env）
_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(_ENV_PATH)

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
_config_cache = None


def load_config() -> dict:
    """加载完整配置（带缓存）"""
    global _config_cache
    if _config_cache is None:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = json.load(f)
    return _config_cache


def reload_config():
    """清除缓存并重新加载配置"""
    global _config_cache
    _config_cache = None
    load_dotenv(_ENV_PATH, override=True)
    return load_config()


def get_api_key(provider: str) -> str:
    """获取指定厂商的 API Key，环境变量优先"""
    env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "zhipu": "ZHIPU_API_KEY",
        "qwen": "QWEN_API_KEY",
        "siliconflow": "SILICONFLOW_API_KEY",
        "custom": "CUSTOM_API_KEY",
        "modelscope": "MODELSCOPE_API_KEY",
    }
    env_key = env_map.get(provider, "")
    val = os.getenv(env_key, "") if env_key else ""
    if val:
        return val
    config = load_config()
    return config.get("api_keys", {}).get(provider, "")


def get_api_url(provider: str) -> str:
    """获取指定厂商的 API URL"""
    config = load_config()
    api_urls = config.get("api_urls", {})
    return api_urls.get(provider, "")


def get_vl_config() -> dict:
    """获取视觉模型提取器配置，环境变量优先"""
    config = load_config()
    vl = dict(config.get("vl_extractor", {}))
    env_key = os.getenv("VL_API_KEY")
    if env_key:
        vl["api_key"] = env_key
    env_url = os.getenv("VL_API_URL")
    if env_url:
        vl["api_url"] = env_url
    env_model = os.getenv("VL_MODEL")
    if env_model:
        vl["model"] = env_model
    return vl


def get_database_url() -> str:
    """获取数据库连接URL，环境变量优先"""
    env_val = os.getenv("DATABASE_URL", "")
    if env_val:
        return env_val
    config = load_config()
    return config.get("database", {}).get("url", "")


def get_jwt_secret() -> str:
    """获取JWT密钥，环境变量优先"""
    env_val = os.getenv("JWT_SECRET_KEY", "")
    if env_val:
        return env_val
    config = load_config()
    return config.get("jwt", {}).get("secret_key", "")


def get_embedding_config() -> dict:
    """获取 Embedding 完整配置，环境变量优先"""
    config = load_config()
    emb = dict(config.get("embedding", {}))
    env_key = os.getenv("EMBEDDING_API_KEY")
    if env_key:
        emb["api_key"] = env_key
    env_url = os.getenv("EMBEDDING_API_URL")
    if env_url:
        emb["api_url"] = env_url
    env_model = os.getenv("EMBEDDING_MODEL")
    if env_model:
        emb["model"] = env_model
    env_dims = os.getenv("EMBEDDING_DIMENSIONS")
    if env_dims:
        emb["dimensions"] = int(env_dims)
    return emb
