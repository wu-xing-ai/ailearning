"""
配置管理模块 - 管理Ollama服务配置
"""
import json
import os
from typing import Dict


class OllamaConfig:
    """Ollama配置管理类"""

    DEFAULT_CONFIG = {
        "model": "llama3.2",
        "base_url": "http://localhost:11434",
        "temperature": 0.7,
        "max_tokens": 2048
    }

    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为backend目录
        """
        if config_dir is None:
            # 获取当前文件所在目录的父目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.dirname(current_dir)

        self.config_file = os.path.join(config_dir, "ollama_config.json")
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """
        从文件加载配置

        Returns:
            配置字典
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置
                    return {**self.DEFAULT_CONFIG, **loaded_config}
            except (json.JSONDecodeError, IOError):
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def save_config(self, config: Dict) -> bool:
        """
        保存配置到文件

        Args:
            config: 要保存的配置字典

        Returns:
            保存是否成功
        """
        try:
            # 合并现有配置
            self.config = {**self.config, **config}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"保存配置失败: {e}")
            return False

    def get_config(self) -> Dict:
        """
        获取当前配置

        Returns:
            配置字典
        """
        return self.config.copy()

    def update_config(self, **kwargs) -> bool:
        """
        更新配置项

        Args:
            **kwargs: 要更新的配置项

        Returns:
            更新是否成功
        """
        self.config.update(kwargs)
        return self.save_config(self.config)

    def reset_config(self) -> bool:
        """
        重置为默认配置

        Returns:
            重置是否成功
        """
        self.config = self.DEFAULT_CONFIG.copy()
        return self.save_config(self.config)

    @property
    def model(self) -> str:
        """获取当前模型名称"""
        return self.config.get("model", self.DEFAULT_CONFIG["model"])

    @property
    def base_url(self) -> str:
        """获取Ollama服务地址"""
        return self.config.get("base_url", self.DEFAULT_CONFIG["base_url"])

    @property
    def temperature(self) -> float:
        """获取温度参数"""
        return self.config.get("temperature", self.DEFAULT_CONFIG["temperature"])

    @property
    def max_tokens(self) -> int:
        """获取最大token数"""
        return self.config.get("max_tokens", self.DEFAULT_CONFIG["max_tokens"])
