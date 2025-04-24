import os
import yaml
from pydantic import ValidationError
from typing import Optional

from core.pydantic_models.config_settings import ConfigSettings
from utils.helpers import get_project_root # 프로젝트 루트 경로 함수 사용

# 프로젝트 루트 경로 계산
PROJECT_ROOT = get_project_root()
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "src" / "config.yml"

class ConfigService:
    def __init__(self, config_path: str = str(DEFAULT_CONFIG_PATH)):
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
            # Pydantic 모델을 dict로 변환 (기본값 포함, None 값 제외 안 함)
            config_data = settings.model_dump(mode='python')
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                # default_flow_style=False 로 블록 스타일 유지, allow_unicode=True 로 유니코드 문자 지원
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            print(f"Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"Error saving configuration to {self.config_path}: {e}")

    def get_settings(self) -> ConfigSettings:
        """Returns the current configuration settings."""
        # 필요시 매번 파일을 다시 로드하도록 수정 가능
        # return self._load_config()
        return self._settings

    def update_settings(self, **kwargs):
        """Updates specific configuration settings and saves them."""
        try:
            # 현재 설정 복사 후 업데이트 적용
            updated_data = self._settings.model_copy(update=kwargs).model_dump()
            # 업데이트된 데이터로 새 Pydantic 모델 생성 (재검증)
            self._settings = ConfigSettings(**updated_data)
            # 변경된 설정 저장
            self._save_config(self._settings)
            print("Configuration updated successfully.")
        except ValidationError as e:
            print(f"Configuration update validation error: {e}")
        except Exception as e:
            print(f"Error updating configuration: {e}")
