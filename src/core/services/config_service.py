import os
import yaml
from pydantic import ValidationError
from typing import Optional

# 변경된 경로에서 import
from core.pydantic_models.config_settings import ConfigSettings
from utils.helpers import get_resource_path # get_resource_path 대신 프로젝트 루트 기반 경로 사용 고려

# 프로젝트 루트 경로 계산 (config_service.py 위치 기준)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
DEFAULT_CONFIG_PATH = os.path.join(PROJECT_ROOT, "src", "config.yml")

class ConfigService:
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self._settings = self._load_config()

    def _load_config(self) -> ConfigSettings:
        """Loads configuration from the YAML file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
                # Pydantic 모델로 유효성 검사 및 변환
                settings = ConfigSettings(**config_data)
                print(f"Configuration loaded from {self.config_path}")
            else:
                print(f"Config file not found at {self.config_path}. Using default settings.")
                settings = ConfigSettings() # 기본값 사용
                self._save_config(settings) # 기본 설정 파일 생성
            return settings
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {self.config_path}: {e}. Using default settings.")
            return ConfigSettings()
        except ValidationError as e:
            print(f"Configuration validation error: {e}. Using default settings.")
            # 유효성 검사 실패 시 기본값 사용 또는 오류 처리 강화 가능
            return ConfigSettings()
        except Exception as e:
            print(f"Unexpected error loading config: {e}. Using default settings.")
            return ConfigSettings()

    def _save_config(self, settings: ConfigSettings):
        """Saves the current configuration to the YAML file."""
        try:
            # Pydantic 모델을 dict로 변환 (기본값 포함)
            config_data = settings.model_dump(mode='python')
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            print(f"Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"Error saving configuration to {self.config_path}: {e}")

    def get_settings(self) -> ConfigSettings:
        """Returns the current configuration settings."""
        return self._settings

    def update_settings(self, **kwargs):
        """Updates specific configuration settings and saves them."""
        try:
            updated_data = self._settings.model_copy(update=kwargs)
            self._settings = ConfigSettings(**updated_data.model_dump()) # 재검증
            self._save_config(self._settings)
            print("Configuration updated successfully.")
        except ValidationError as e:
            print(f"Configuration update validation error: {e}")
        except Exception as e:
            print(f"Error updating configuration: {e}")

# 전역 인스턴스 또는 DI 컨테이너를 통해 서비스 제공 고려
# 예시: config_service = ConfigService()
