import pytest
import psycopg2
from typing import Generator
from unittest.mock import patch, MagicMock

# 테스트 대상 모듈 임포트
from core.services.db_service import DbService, DB_CONFIG
from core.pydantic_models.ssh_config import SshConnectionConfig

# 테스트용 DB 설정 (기존 DB와 분리하거나, 테스트 후 정리 필요)
# 여기서는 Mocking을 주로 사용

@pytest.fixture
def mock_db_connection() -> Generator[MagicMock, None, None]:
    """psycopg2.connect와 cursor를 Mocking하는 fixture"""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None # 기본적으로는 아무것도 반환하지 않음
        mock_cursor.fetchall.return_value = []   # 기본적으로는 빈 리스트 반환
        mock_cursor.rowcount = 0               # 기본적으로는 영향받은 행 없음
        yield mock_cursor # 테스트 함수에서 cursor mock 사용 가능

@pytest.fixture
def db_service(mock_db_connection) -> DbService:
    """Mocking된 연결을 사용하는 DbService 인스턴스를 생성하는 fixture"""
    # DbService 초기화 시 connect()가 호출되므로 Mocking된 상태에서 생성
    service = DbService(db_config=DB_CONFIG) # 실제 DB 접속 시도 안 함
    # Mocking된 cursor 주입 (선택적, _execute_query 내부에서 cursor 생성)
    # service.connection.cursor.return_value = mock_db_connection
    return service

# --- 테스트 케이스 ---

def test_add_ssh_connection_success(db_service: DbService, mock_db_connection: MagicMock):
    """add_ssh_connection 성공 케이스 테스트"""
    mock_db_connection.fetchone.return_value = (1,) # RETURNING id 결과 Mocking
    config = SshConnectionConfig(
        alias="test_server", hostname="192.168.1.100", port=22, username="testuser",
        auth_method="password", password="testpassword"
    )
    new_id = db_service.add_ssh_connection(config)

    assert new_id == 1
    mock_db_connection.execute.assert_called_once()
    # SQL 쿼리 및 파라미터 검증 (더 상세하게)
    call_args = mock_db_connection.execute.call_args
    assert "INSERT INTO ssh_connections" in call_args[0][0]
    assert call_args[0][1] == (
        "test_server", "192.168.1.100", 22, "testuser", "password", "testpassword", None
    )
    db_service.connection.commit.assert_called_once()

def test_add_ssh_connection_duplicate_alias(db_service: DbService, mock_db_connection: MagicMock):
    """add_ssh_connection 별칭 중복 (IntegrityError) 케이스 테스트"""
    mock_db_connection.execute.side_effect = psycopg2.IntegrityError("duplicate key value violates unique constraint")
    config = SshConnectionConfig(
        alias="existing_alias", hostname="1.1.1.1", port=22, username="user",
        auth_method="key", key_path="/path/to/key"
    )
    new_id = db_service.add_ssh_connection(config)

    assert new_id is None
    db_service.connection.rollback.assert_called_once() # 롤백 확인

def test_get_ssh_connection_found(db_service: DbService, mock_db_connection: MagicMock):
    """get_ssh_connection 데이터 찾음 케이스 테스트"""
    mock_row = {
        "id": 5, "alias": "found_server", "hostname": "example.com", "port": 2222,
        "username": "found_user", "auth_method": "key", "password": None, "key_path": "~/.ssh/id_rsa"
    }
    # _execute_query가 딕셔너리를 반환하도록 Mocking
    with patch.object(db_service, '_execute_query', return_value=mock_row) as mock_execute:
        config = db_service.get_ssh_connection(5)

        assert config is not None
        assert config.id == 5
        assert config.alias == "found_server"
        assert config.auth_method == "key"
        assert config.key_path == "~/.ssh/id_rsa"
        mock_execute.assert_called_once_with("SELECT * FROM ssh_connections WHERE id = %s;", (5,), fetch_one=True)

def test_get_ssh_connection_not_found(db_service: DbService, mock_db_connection: MagicMock):
    """get_ssh_connection 데이터 없음 케이스 테스트"""
    with patch.object(db_service, '_execute_query', return_value=None) as mock_execute:
        config = db_service.get_ssh_connection(99)
        assert config is None
        mock_execute.assert_called_once_with("SELECT * FROM ssh_connections WHERE id = %s;", (99,), fetch_one=True)

def test_list_ssh_connections_success(db_service: DbService, mock_db_connection: MagicMock):
    """list_ssh_connections 성공 케이스 테스트"""
    mock_rows = [
        {"id": 1, "alias": "server_a", "hostname": "a.com", "port": 22, "username": "user_a", "auth_method": "password", "password": "pwd", "key_path": None},
        {"id": 2, "alias": "server_b", "hostname": "b.com", "port": 22, "username": "user_b", "auth_method": "key", "password": None, "key_path": "/key/b"},
    ]
    with patch.object(db_service, '_execute_query', return_value=mock_rows) as mock_execute:
        connections = db_service.list_ssh_connections()

        assert len(connections) == 2
        assert connections[0].alias == "server_a"
        assert connections[1].auth_method == "key"
        mock_execute.assert_called_once_with("SELECT * FROM ssh_connections ORDER BY alias;", fetch_all=True)

def test_list_ssh_connections_empty(db_service: DbService, mock_db_connection: MagicMock):
    """list_ssh_connections 결과 없음 케이스 테스트"""
    with patch.object(db_service, '_execute_query', return_value=[]) as mock_execute:
        connections = db_service.list_ssh_connections()
        assert len(connections) == 0
        mock_execute.assert_called_once_with("SELECT * FROM ssh_connections ORDER BY alias;", fetch_all=True)

def test_update_ssh_connection_success(db_service: DbService, mock_db_connection: MagicMock):
    """update_ssh_connection 성공 케이스 테스트"""
    mock_db_connection.rowcount = 1 # 업데이트 성공 시 1 반환 가정
    config = SshConnectionConfig(
        id=3, alias="updated_alias", hostname="updated.host", port=23, username="updated_user",
        auth_method="key", key_path="/new/path"
    )
    success = db_service.update_ssh_connection(config)

    assert success is True
    mock_db_connection.execute.assert_called_once()
    call_args = mock_db_connection.execute.call_args
    assert "UPDATE ssh_connections SET" in call_args[0][0]
    assert call_args[0][1] == (
        "updated_alias", "updated.host", 23, "updated_user", "key", None, "/new/path", 3
    )
    db_service.connection.commit.assert_called_once()

def test_update_ssh_connection_not_found(db_service: DbService, mock_db_connection: MagicMock):
    """update_ssh_connection 대상 없음 케이스 테스트"""
    mock_db_connection.rowcount = 0 # 영향받은 행 없음
    config = SshConnectionConfig(
        id=99, alias="not_found", hostname="nf.host", port=22, username="nf_user",
        auth_method="password", password="pwd"
    )
    success = db_service.update_ssh_connection(config)

    assert success is False
    db_service.connection.commit.assert_called_once() # commit은 호출됨

def test_update_ssh_connection_missing_id(db_service: DbService):
    """update_ssh_connection ID 누락 케이스 테스트"""
    config = SshConnectionConfig(
        alias="no_id", hostname="no.id", port=22, username="no_id_user",
        auth_method="password", password="pwd"
    )
    success = db_service.update_ssh_connection(config)
    assert success is False

def test_delete_ssh_connection_success(db_service: DbService, mock_db_connection: MagicMock):
    """delete_ssh_connection 성공 케이스 테스트"""
    mock_db_connection.rowcount = 1
    success = db_service.delete_ssh_connection(7)

    assert success is True
    mock_db_connection.execute.assert_called_once_with("DELETE FROM ssh_connections WHERE id = %s;", (7,))
    db_service.connection.commit.assert_called_once()

def test_delete_ssh_connection_not_found(db_service: DbService, mock_db_connection: MagicMock):
    """delete_ssh_connection 대상 없음 케이스 테스트"""
    mock_db_connection.rowcount = 0
    success = db_service.delete_ssh_connection(99)

    assert success is False
    db_service.connection.commit.assert_called_once()
