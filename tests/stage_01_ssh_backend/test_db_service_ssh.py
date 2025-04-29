import pytest
import psycopg2
from typing import Generator
from unittest.mock import patch, MagicMock

# Add src directory to sys.path for module resolution
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

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
        mock_conn.closed = False # ConnectionError 방지를 위해 closed 속성 설정
        mock_cursor.fetchone.return_value = None # 기본적으로는 아무것도 반환하지 않음
        mock_cursor.fetchall.return_value = []   # 기본적으로는 빈 리스트 반환
        mock_cursor.rowcount = 0               # 기본적으로는 영향받은 행 없음
        yield mock_cursor # 테스트 함수에서 cursor mock 사용 가능

@pytest.fixture
def db_service(mock_db_connection) -> DbService:
    """Mocking된 연결을 사용하는 DbService 인스턴스를 생성하는 fixture"""
    # DbService 초기화 시 connect()가 호출되므로 Mocking된 상태에서 생성
    service = DbService(db_config=DB_CONFIG) # 실제 DB 접속 시도 안 함
    # 생성된 service의 connection이 mock_conn을 가리키는지 확인 (선택적)
    # assert isinstance(service.connection, MagicMock)
    # assert service.connection.closed == False
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
    # IntegrityError는 _execute_query 내부의 cursor.execute에서 발생해야 함
    mock_db_connection.execute.side_effect = psycopg2.IntegrityError("duplicate key value violates unique constraint")
    config = SshConnectionConfig(
        alias="existing_alias", hostname="1.1.1.1", port=22, username="user",
        auth_method="key", key_path="/path/to/key"
    )
    # add_ssh_connection은 내부적으로 _execute_query를 호출하고 예외를 처리함
    new_id = db_service.add_ssh_connection(config)

    assert new_id is None
    # IntegrityError 발생 시 rollback이 호출되어야 함
    db_service.connection.rollback.assert_called_once()
    db_service.connection.commit.assert_not_called() # commit은 호출되지 않아야 함

def test_get_ssh_connection_found(db_service: DbService, mock_db_connection: MagicMock):
    """get_ssh_connection 데이터 찾음 케이스 테스트"""
    mock_row_tuple = (5, "found_server", "example.com", 2222, "found_user", "key", None, "~/.ssh/id_rsa", datetime.datetime.now(), datetime.datetime.now())
    mock_description = [
        ('id', None, None, None, None, None, None),
        ('alias', None, None, None, None, None, None),
        ('hostname', None, None, None, None, None, None),
        ('port', None, None, None, None, None, None),
        ('username', None, None, None, None, None, None),
        ('auth_method', None, None, None, None, None, None),
        ('password', None, None, None, None, None, None),
        ('key_path', None, None, None, None, None, None),
        ('created_at', None, None, None, None, None, None),
        ('updated_at', None, None, None, None, None, None),
    ]
    mock_db_connection.fetchone.return_value = mock_row_tuple
    mock_db_connection.description = mock_description

    config = db_service.get_ssh_connection(5)

    assert config is not None
    assert config.id == 5
    assert config.alias == "found_server"
    assert config.auth_method == "key"
    assert config.key_path == "~/.ssh/id_rsa"
    # _execute_query 호출 검증
    mock_db_connection.execute.assert_called_once_with("SELECT * FROM ssh_connections WHERE id = %s;", (5,))


def test_get_ssh_connection_not_found(db_service: DbService, mock_db_connection: MagicMock):
    """get_ssh_connection 데이터 없음 케이스 테스트"""
    mock_db_connection.fetchone.return_value = None # 데이터 없음 Mocking
    mock_db_connection.description = None # fetchone이 None이면 description도 없을 수 있음

    config = db_service.get_ssh_connection(99)

    assert config is None
    mock_db_connection.execute.assert_called_once_with("SELECT * FROM ssh_connections WHERE id = %s;", (99,))


def test_list_ssh_connections_success(db_service: DbService, mock_db_connection: MagicMock):
    """list_ssh_connections 성공 케이스 테스트"""
    mock_rows_tuples = [
        (1, "server_a", "a.com", 22, "user_a", "password", "pwd", None, datetime.datetime.now(), datetime.datetime.now()),
        (2, "server_b", "b.com", 22, "user_b", "key", None, "/key/b", datetime.datetime.now(), datetime.datetime.now()),
    ]
    mock_description = [ # 컬럼 순서 중요
        ('id',), ('alias',), ('hostname',), ('port',), ('username',), ('auth_method',), ('password',), ('key_path',), ('created_at',), ('updated_at',)
    ]
    mock_db_connection.fetchall.return_value = mock_rows_tuples
    mock_db_connection.description = mock_description

    connections = db_service.list_ssh_connections()

    assert len(connections) == 2
    assert connections[0].alias == "server_a"
    assert connections[1].auth_method == "key"
    # _execute_query 호출 시 params가 None으로 전달됨
    mock_db_connection.execute.assert_called_once_with("SELECT * FROM ssh_connections ORDER BY alias;", None)


def test_list_ssh_connections_empty(db_service: DbService, mock_db_connection: MagicMock):
    """list_ssh_connections 결과 없음 케이스 테스트"""
    mock_db_connection.fetchall.return_value = []
    mock_db_connection.description = None # 결과 없으면 description 없을 수 있음

    connections = db_service.list_ssh_connections()

    assert len(connections) == 0
    # _execute_query 호출 시 params가 None으로 전달됨
    mock_db_connection.execute.assert_called_once_with("SELECT * FROM ssh_connections ORDER BY alias;", None)


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
    # 파라미터 순서 확인 (SQL 쿼리 순서와 일치해야 함)
    expected_params = (
        "updated_alias", "updated.host", 23, "updated_user", "key", None, "/new/path", 3
    )
    assert call_args[0][1] == expected_params
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
    mock_db_connection.execute.assert_called_once() # execute는 호출됨
    db_service.connection.commit.assert_called_once() # commit은 호출됨 (rowcount 0이어도)


def test_update_ssh_connection_missing_id(db_service: DbService):
    """update_ssh_connection ID 누락 케이스 테스트"""
    config = SshConnectionConfig(
        alias="no_id", hostname="no.id", port=22, username="no_id_user",
        auth_method="password", password="pwd"
    )
    success = db_service.update_ssh_connection(config)
    assert success is False
    # ID 없으면 _execute_query 호출 안 함 -> commit/rollback도 호출 안 됨
    db_service.connection.commit.assert_not_called()
    db_service.connection.rollback.assert_not_called()


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
    mock_db_connection.execute.assert_called_once_with("DELETE FROM ssh_connections WHERE id = %s;", (99,))
    db_service.connection.commit.assert_called_once() # commit은 호출됨 (rowcount 0이어도)

# --- datetime import 추가 ---
import datetime
# ---------------------------

