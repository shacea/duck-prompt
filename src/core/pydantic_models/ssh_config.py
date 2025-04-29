from pydantic import BaseModel, Field, validator, FilePath, field_validator, ConfigDict # ConfigDict 추가
from typing import Optional, Literal

class SshConnectionConfig(BaseModel):
    """
    Represents the configuration for an SSH connection.
    """
    id: Optional[int] = None # DB에서 자동 생성되는 ID
    alias: str = Field(..., min_length=1, description="사용자가 식별하기 위한 연결 별칭")
    hostname: str = Field(..., description="SSH 서버 호스트 주소 (IP 또는 도메인)")
    port: int = Field(22, gt=0, le=65535, description="SSH 서버 포트 번호")
    username: str = Field(..., min_length=1, description="SSH 접속 사용자명")
    auth_method: Literal["password", "key"] = Field(..., description="인증 방식 ('password' 또는 'key')")
    password: Optional[str] = Field(None, description="비밀번호 인증 시 사용될 비밀번호 (주의: 저장 시 보안 고려 필요)")
    key_path: Optional[str] = Field(None, description="키 파일 인증 시 사용될 개인 키 파일 경로")
    # key_passphrase: Optional[str] = Field(None, description="개인 키 파일에 암호가 설정된 경우 사용") # 필요 시 추가

    @field_validator('password', 'key_path')
    @classmethod
    def check_auth_method_fields(cls, v, info):
        """인증 방식에 따라 필요한 필드가 있는지 확인합니다."""
        auth_method = info.data.get('auth_method')
        field_name = info.field_name

        if auth_method == 'password' and field_name == 'password' and not v:
            raise ValueError("비밀번호 인증 방식에는 비밀번호가 필요합니다.")
        if auth_method == 'key' and field_name == 'key_path' and not v:
            raise ValueError("키 파일 인증 방식에는 키 파일 경로가 필요합니다.")
        # 인증 방식과 다른 필드는 None이어야 함 (선택적 강화)
        # if auth_method == 'password' and field_name == 'key_path' and v:
        #     raise ValueError("비밀번호 인증 시 키 파일 경로는 설정할 수 없습니다.")
        # if auth_method == 'key' and field_name == 'password' and v:
        #     raise ValueError("키 파일 인증 시 비밀번호는 설정할 수 없습니다.")
        return v

    # key_path 유효성 검사 (파일 존재 여부 등)는 서비스 레이어에서 처리하는 것이 더 적합할 수 있음

    # Pydantic V2: Config 클래스 대신 model_config 사용
    model_config = ConfigDict(
        validate_assignment=True,
        extra='ignore' # DB 로드 시 추가 필드 무시
    )

