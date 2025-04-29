import pytest
from unittest.mock import MagicMock, patch

# 테스트 대상 모듈 임포트
from core.services.ssh_config_service import SshConfigService
from core.services.db_service import DbService
from core.pydantic_models.ssh_config import SshConnectionConfig

@pytest.fixture
def mock_db_service() -> MagicMock:
    """DbService를 Mocking하는 fixture"""
    return MagicMock(spec=DbService)

@pytest.fixture
def ssh_config_service(mock_db_service: MagicMock) -> SshConfigService:
    """Mocking된 DbService를 사용하는 SshConfigService 인스턴스 생성"""
    return SshConfigService(db_service=mock_db_service)

# --- 테스트 케이스 ---

def test_add_connection_success(ssh_config_service: SshConfigService, mock_db_service: MagicMock):
    """add_connection 성공 케이스"""
    config_data = {
        "alias": "new_server", "hostname": "new.host", "port": 22, "username": "new_user",
        "auth_method": "password", "password": "new_password"
    }
    config = SshConnectionConfig(**config_data)
    mock_db_service.add_ssh_connection.return_value = 10 # 새 ID 반환 가정

    new_id = ssh_config_service.add_connection(config)

    assert new_id == 10
    # add_ssh_connection 호출 시 id가 None으로 설정되었는지 확인
    mock_db_service.add_ssh_connection.assert_called_once()
    call_arg = mock_db_service.add_ssh_connection.call_args[0][0]
    assert isinstance(call_arg, SshConnectionConfig)
    assert call_arg.id is None
    assert call_arg.alias == "new_server"

def test_add_connection_failure(ssh_config_service: SshConfigService, mock_db_service: MagicMock):
    """add_connection 실패 케이스 (DB 오류)"""
    config = SshConnectionConfig(
        alias="fail_server", hostname="fail.host", port=22, username="fail_user",
        auth_method="key", key_path="/key/fail"
    )
    mock_db_service.add_ssh_connection.return_value = None # 실패 시 None 반환 가정

    new_id = ssh_config_service.add_connection(config)

    assert new_id is None
    mock_db_service.add_ssh_connection.assert_called_once_with(config)

def test_get_connection_found(ssh_config_service: SshConfigService, mock_db_service: MagicMock):
    """get_connection 데이터 찾음 케이스"""
    mock_config = SshConnectionConfig(
        id=1, alias="get_server", hostname="get.host", port=22, username="get_user",
        auth_method="password", password="pwd"
    )
    mock_db_service.get_ssh_connection.return_value = mock_config

    result = ssh_config_service.get_connection(1)

    assert result == mock_config
    mock_db_service.get_ssh_connection.assert_called_once_with(1)

def test_get_connection_not_found(ssh_config_service: SshConfigService, mock_db_service: MagicMock):
    """get_connection 데이터 없음 케이스"""
    mock_db_service.get_ssh_connection.return_value = None

    result = ssh_config_service.get_connection(99)

    assert result is None
    mock_db_service.get_ssh_connection.assert_called_once_with(99)

def test_list_connections_success(ssh_config_service: SshConfigService, mock_db_service: MagicMock):
    """list_connections 성공 케이스"""
    mock_list = [
        SshConnectionConfig(id=1, alias="a", hostname="a.com", port=22, username="ua", auth_method="password", password="p"),
        SshConnectionConfig(id=2, alias="b", hostname="b.com", port=22, username="ub", auth_method="key", key_path="/k"),
    ]
    mock_db_service.list_ssh_connections.return_value = mock_list

    result = ssh_config_service.list_connections()

    assert result == mock_list
    mock_db_service.list_ssh_connections.assert_called_once()

def test_list_connections_empty(ssh_config_service: SshConfigService, mock_db_service: MagicMock):
    """list_connections 결과 없음 케이스"""
    mock_db_service.list_ssh_connections.return_value = []

    result = ssh_config_service.list_connections()

    assert result == []
    mock_db_service.list_ssh_connections.assert_called_once()

def test_update_connection_success(ssh_config_service: SshConfigService, mock_db_service: MagicMock):
    """update_connection 성공 케이스"""
    config = SshConnectionConfig(
        id=5, alias="update_server", hostname="update.host", port=22, username="update_user",
        auth_method="key", key_path="/update/key"
    )
    mock_db_service.update_ssh_connection.return_value = True

    success = ssh_config_service.update_connection(config)

    assert success is True
    mock_db_service.update_ssh_connection.assert_called_once_with(config)

def test_update_connection_missing_id(ssh_config_service: SshConfigService, mock_db_service: MagicMock):
    """update_connection ID 누락 케이스"""
    config = SshConnectionConfig(
        alias="no_id_update", hostname="no.id", port=22, username="no_id_user",
        auth_method="password", password="pwd"
    ) # id가 None
    success = ssh_config_service.update_connection(config)

    assert success is False
    mock_db_service.update_ssh_connection.assert_not_called() # ID 없으면 DB 호출 안 함

def test_update_connection_failure(ssh_config_service: SshConfigService, mock_db_service: MagicMock):
    """update_connection 실패 케이스 (DB 오류)"""
    config = SshConnectionConfig(
        id=6, alias="fail_update", hostname="fail.up", port=22, username="fail_up_user",
        auth_method="password", password="pwd"
    )
    mock_db_service.update_ssh_connection.return_value = False

    success = ssh_config_service.update_connection(config)

    assert success is False
    mock_db_service.update_ssh_connection.assert_called_once_with(config)

def test_delete_connection_success(ssh_config_service: SshConfigService, mock_db_service: MagicMock):
    """delete_connection 성공 케이스"""
    mock_db_service.delete_ssh_connection.return_value = True

    success = ssh_config_service.delete_connection(7)

    assert success is True
    mock_db_service.delete_ssh_connection.assert_called_once_with(7)

def test_delete_connection_failure(ssh_config_service: SshConfigService, mock_db_service: MagicMock):
    """delete_connection 실패 케이스 (DB 오류)"""
    mock_db_service.delete_ssh_connection.return_value = False

    success = ssh_config_service.delete_connection(8)

    assert success is False
    mock_db_service.delete_ssh_connection.assert_called_once_with(8)

def test_get_connection_by_alias_found(ssh_config_service: SshConfigService, mock_db_service: MagicMock):
    """get_connection_by_alias 데이터 찾음 케이스"""
    mock_list = [
        SshConnectionConfig(id=1, alias="a", hostname="a.com", port=22, username="ua", auth_method="password", password="p"),
        SshConnectionConfig(id=2, alias="b", hostname="b.com", port=22, username="ub", auth_method="key", key_path="/k"),
    ]
    mock_db_service.list_ssh_connections.return_value = mock_list

    result = ssh_config_service.get_connection_by_alias("b")

    assert result is not None
    assert result.id == 2
    assert result.alias == "b"
    mock_db_service.list_ssh_connections.assert_called_once()

def test_get_connection_by_alias_not_found(ssh_config_service: SshConfigService, mock_db_service: MagicMock):
    """get_connection_by_alias 데이터 없음 케이스"""
    mock_db_service.list_ssh_connections.return_value = []

    result = ssh_config_service.get_connection_by_alias("not_exist")

    assert result is None
    mock_db_service.list_ssh_connections.assert_called_once()
