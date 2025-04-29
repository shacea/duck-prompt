import pytest
import os
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import QThread, QSignalSpy # QSignalSpy 추가

# 테스트 대상 모듈 임포트
from ui.settings_dialog import SshConnectionTester # Worker 클래스
from core.pydantic_models.ssh_config import SshConnectionConfig

# paramiko Mocking (실제 연결 시도 방지)
# pytest-mock-ssh 같은 라이브러리 사용 고려 가능
@pytest.fixture(autouse=True)
def mock_paramiko():
    """paramiko.SSHClient를 Mocking하여 실제 네트워크 연결 방지"""
    with patch('paramiko.SSHClient', autospec=True) as mock_ssh_client_class:
        mock_client_instance = MagicMock()
        mock_ssh_client_class.return_value = mock_client_instance
        yield mock_client_instance # 테스트 함수에서 client instance mock 사용 가능

# --- 테스트 케이스 ---

@pytest.mark.qt
def test_ssh_connection_tester_success_password(qtbot):
    """비밀번호 인증 성공 시그널 테스트"""
    config = SshConnectionConfig(
        alias="pwd_success", hostname="testhost", port=22, username="testuser",
        auth_method="password", password="goodpassword"
    )
    tester = SshConnectionTester(config)
    spy_finished = QSignalSpy(tester.finished) # 시그널 스파이 생성

    # 스레드에서 실행 (UI 스레드 블로킹 없이)
    thread = QThread()
    tester.moveToThread(thread)
    thread.started.connect(tester.run)
    thread.start()

    # 시그널 대기 (timeout 설정)
    assert spy_finished.wait(1000), "Signal 'finished' was not emitted" # 1초 대기
    thread.quit()
    thread.wait()

    # 시그널 결과 확인
    assert len(spy_finished) == 1
    result_args = spy_finished[0] # 첫 번째 시그널의 인자 리스트
    assert result_args[0] is True # 성공 여부
    assert "성공" in result_args[1] # 메시지

@pytest.mark.qt
def test_ssh_connection_tester_success_key(qtbot, mock_paramiko):
    """키 파일 인증 성공 시그널 테스트"""
    # 임시 키 파일 생성 (테스트 목적)
    key_path = "temp_test_key.pem"
    with open(key_path, "w") as f:
        f.write("-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----")

    config = SshConnectionConfig(
        alias="key_success", hostname="keyhost", port=22, username="keyuser",
        auth_method="key", key_path=key_path
    )
    tester = SshConnectionTester(config)
    spy_finished = QSignalSpy(tester.finished)

    thread = QThread()
    tester.moveToThread(thread)
    thread.started.connect(tester.run)
    thread.start()

    assert spy_finished.wait(1000)
    thread.quit()
    thread.wait()

    assert len(spy_finished) == 1
    result_args = spy_finished[0]
    assert result_args[0] is True
    assert "성공" in result_args[1]

    # paramiko.connect 호출 시 key_filename 인자 확인
    mock_paramiko.connect.assert_called_once()
    call_kwargs = mock_paramiko.connect.call_args.kwargs
    assert call_kwargs.get("key_filename") == os.path.abspath(key_path)

    # 임시 키 파일 삭제
    os.remove(key_path)


@pytest.mark.qt
def test_ssh_connection_tester_auth_failure(qtbot, mock_paramiko):
    """인증 실패 시그널 테스트"""
    # paramiko.connect 호출 시 AuthenticationException 발생하도록 설정
    mock_paramiko.connect.side_effect = paramiko.AuthenticationException("Auth failed")

    config = SshConnectionConfig(
        alias="auth_fail", hostname="failhost", port=22, username="wronguser",
        auth_method="password", password="badpassword"
    )
    tester = SshConnectionTester(config)
    spy_finished = QSignalSpy(tester.finished)

    thread = QThread()
    tester.moveToThread(thread)
    thread.started.connect(tester.run)
    thread.start()

    assert spy_finished.wait(1000)
    thread.quit()
    thread.wait()

    assert len(spy_finished) == 1
    result_args = spy_finished[0]
    assert result_args[0] is False
    assert "인증 실패" in result_args[1]

@pytest.mark.qt
def test_ssh_connection_tester_key_file_not_found(qtbot, mock_paramiko):
    """키 파일 없음 오류 시그널 테스트"""
    config = SshConnectionConfig(
        alias="key_not_found", hostname="keyhost", port=22, username="keyuser",
        auth_method="key", key_path="/non/existent/path/key.pem"
    )
    tester = SshConnectionTester(config)
    spy_finished = QSignalSpy(tester.finished)

    thread = QThread()
    tester.moveToThread(thread)
    thread.started.connect(tester.run)
    thread.start()

    assert spy_finished.wait(1000)
    thread.quit()
    thread.wait()

    assert len(spy_finished) == 1
    result_args = spy_finished[0]
    assert result_args[0] is False
    assert "키 파일 오류" in result_args[1]
    assert "not found" in result_args[1]
    # connect는 호출되지 않아야 함
    mock_paramiko.connect.assert_not_called()

@pytest.mark.qt
def test_ssh_connection_tester_connection_error(qtbot, mock_paramiko):
    """일반 연결 오류 시그널 테스트"""
    mock_paramiko.connect.side_effect = paramiko.SSHException("Connection refused")

    config = SshConnectionConfig(
        alias="conn_error", hostname="unreachable", port=22, username="user",
        auth_method="password", password="pwd"
    )
    tester = SshConnectionTester(config)
    spy_finished = QSignalSpy(tester.finished)

    thread = QThread()
    tester.moveToThread(thread)
    thread.started.connect(tester.run)
    thread.start()

    assert spy_finished.wait(1000)
    thread.quit()
    thread.wait()

    assert len(spy_finished) == 1
    result_args = spy_finished[0]
    assert result_args[0] is False
    assert "SSH 오류" in result_args[1]
    assert "Connection refused" in result_args[1]

@pytest.mark.qt
def test_ssh_connection_tester_missing_password(qtbot, mock_paramiko):
    """비밀번호 방식인데 비밀번호 누락 시 오류"""
    config = SshConnectionConfig(
        alias="missing_pwd", hostname="host", port=22, username="user",
        auth_method="password", password=None # 비밀번호 없음
    )
    tester = SshConnectionTester(config)
    spy_finished = QSignalSpy(tester.finished)

    thread = QThread()
    tester.moveToThread(thread)
    thread.started.connect(tester.run)
    thread.start()

    assert spy_finished.wait(1000)
    thread.quit()
    thread.wait()

    assert len(spy_finished) == 1
    result_args = spy_finished[0]
    assert result_args[0] is False
    assert "연결 오류" in result_args[1] # ValueError가 발생
    assert "Password is required" in result_args[1]
    mock_paramiko.connect.assert_not_called()

@pytest.mark.qt
def test_ssh_connection_tester_missing_key_path(qtbot, mock_paramiko):
    """키 방식인데 키 경로 누락 시 오류"""
    config = SshConnectionConfig(
        alias="missing_key", hostname="host", port=22, username="user",
        auth_method="key", key_path=None # 키 경로 없음
    )
    tester = SshConnectionTester(config)
    spy_finished = QSignalSpy(tester.finished)

    thread = QThread()
    tester.moveToThread(thread)
    thread.started.connect(tester.run)
    thread.start()

    assert spy_finished.wait(1000)
    thread.quit()
    thread.wait()

    assert len(spy_finished) == 1
    result_args = spy_finished[0]
    assert result_args[0] is False
    assert "연결 오류" in result_args[1] # ValueError가 발생
    assert "Key file path is required" in result_args[1]
    mock_paramiko.connect.assert_not_called()
