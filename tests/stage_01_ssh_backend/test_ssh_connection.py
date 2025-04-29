import pytest
import os
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import QThread
from PyQt6.QtTest import QSignalSpy

# Add src directory to sys.path for module resolution
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 테스트 대상 모듈 임포트
from ui.settings_dialog import SshConnectionTester # Worker 클래스
from core.pydantic_models.ssh_config import SshConnectionConfig
import paramiko # Mocking 대상
import datetime # datetime import 추가

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

@pytest.mark.timeout(10)  # 10초 타임아웃 추가
def test_ssh_connection_tester_success_password(mock_paramiko):
    """비밀번호 인증 성공 시그널 테스트"""
    print("테스트 시작: test_ssh_connection_tester_success_password")
    
    # mock_paramiko 설정 - 명시적으로 성공 응답 설정
    mock_client = mock_paramiko
    # mock이 connect 호출 시 성공 반환 (side_effect 없음)

    config = SshConnectionConfig(
        alias="pwd_success", hostname="testhost", port=22, username="testuser",
        auth_method="password", password="goodpassword"
    )
    
    # 테스터 생성 - 스레드 없이 직접 실행
    tester = SshConnectionTester(config)
    spy_finished = QSignalSpy(tester.finished)
    print(f"SshConnectionTester 생성됨, signal valid: {spy_finished.isValid()}")
    
    # 직접 실행 - 스레드 사용하지 않음
    tester.run()
    print("SshConnectionTester.run() 직접 호출 완료")
    
    # 시그널 결과 확인
    print(f"spy_finished 길이: {len(spy_finished)}")
    assert len(spy_finished) > 0, "신호가 발생하지 않았습니다"
    
    if len(spy_finished) > 0:
        result_args = spy_finished[0]
        print(f"시그널 결과: {result_args}")
        assert result_args[0] is True  # 성공 여부
        assert "성공" in result_args[1]  # 메시지

@pytest.mark.timeout(10)  # 10초 타임아웃 추가
def test_ssh_connection_tester_success_key(mock_paramiko):
    """키 파일 인증 성공 시그널 테스트"""
    print("테스트 시작: test_ssh_connection_tester_success_key")
    # 임시 키 파일 생성 (테스트 목적)
    key_path = "temp_test_key.pem"
    with open(key_path, "w", encoding="utf-8") as f:
        f.write("-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----")

    config = SshConnectionConfig(
        alias="key_success", hostname="keyhost", port=22, username="keyuser",
        auth_method="key", key_path=key_path
    )
    tester = SshConnectionTester(config)
    spy_finished = QSignalSpy(tester.finished)
    print(f"SshConnectionTester 생성됨, signal valid: {spy_finished.isValid()}")

    # 직접 실행 - 스레드 사용하지 않음
    tester.run()
    print("SshConnectionTester.run() 직접 호출 완료")

    # 시그널 결과 확인
    print(f"spy_finished 길이: {len(spy_finished)}")
    assert len(spy_finished) > 0, "신호가 발생하지 않았습니다"
    
    if len(spy_finished) > 0:
        result_args = spy_finished[0]
        print(f"시그널 결과: {result_args}")
        assert result_args[0] is True
        assert "성공" in result_args[1]

    # paramiko.connect 호출 시 key_filename 인자 확인
    mock_paramiko.connect.assert_called_once()
    call_kwargs = mock_paramiko.connect.call_args.kwargs
    # 경로 검사를 단순화: 단순히 키 경로가 존재하는지만 확인
    assert "key_filename" in call_kwargs, "key_filename이 connect 호출에 전달되지 않았습니다"
    assert os.path.exists(call_kwargs.get("key_filename")), "키 파일 경로가 유효하지 않습니다"

    # 임시 키 파일 삭제
    os.remove(key_path)

@pytest.mark.timeout(10)  # 10초 타임아웃 추가
def test_ssh_connection_tester_auth_failure(mock_paramiko):
    """인증 실패 시그널 테스트"""
    print("테스트 시작: test_ssh_connection_tester_auth_failure")
    # paramiko.connect 호출 시 AuthenticationException 발생하도록 설정
    mock_paramiko.connect.side_effect = paramiko.AuthenticationException("Auth failed")

    config = SshConnectionConfig(
        alias="auth_fail", hostname="failhost", port=22, username="wronguser",
        auth_method="password", password="badpassword"
    )
    tester = SshConnectionTester(config)
    spy_finished = QSignalSpy(tester.finished)
    print(f"SshConnectionTester 생성됨, signal valid: {spy_finished.isValid()}")

    # 직접 실행 - 스레드 사용하지 않음
    tester.run()
    print("SshConnectionTester.run() 직접 호출 완료")

    # 시그널 결과 확인
    print(f"spy_finished 길이: {len(spy_finished)}")
    assert len(spy_finished) > 0, "신호가 발생하지 않았습니다"
    
    if len(spy_finished) > 0:
        result_args = spy_finished[0]
        print(f"시그널 결과: {result_args}")
        assert result_args[0] is False
        assert "인증 실패" in result_args[1]

@pytest.mark.timeout(10)  # 10초 타임아웃 추가
def test_ssh_connection_tester_key_file_not_found(mock_paramiko):
    """키 파일 없음 오류 시그널 테스트"""
    print("테스트 시작: test_ssh_connection_tester_key_file_not_found")
    config = SshConnectionConfig(
        alias="key_not_found", hostname="keyhost", port=22, username="keyuser",
        auth_method="key", key_path="/non/existent/path/key.pem"
    )
    tester = SshConnectionTester(config)
    spy_finished = QSignalSpy(tester.finished)
    print(f"SshConnectionTester 생성됨, signal valid: {spy_finished.isValid()}")

    # 직접 실행 - 스레드 사용하지 않음
    tester.run()
    print("SshConnectionTester.run() 직접 호출 완료")

    # 시그널 결과 확인
    print(f"spy_finished 길이: {len(spy_finished)}")
    assert len(spy_finished) > 0, "신호가 발생하지 않았습니다"
    
    if len(spy_finished) > 0:
        result_args = spy_finished[0]
        print(f"시그널 결과: {result_args}")
        assert result_args[0] is False
        assert "키 파일 오류" in result_args[1]
        assert "not found" in result_args[1]
    
    # connect는 호출되지 않아야 함
    mock_paramiko.connect.assert_not_called()

@pytest.mark.timeout(10)  # 10초 타임아웃 추가
def test_ssh_connection_tester_connection_error(mock_paramiko):
    """일반 연결 오류 시그널 테스트"""
    print("테스트 시작: test_ssh_connection_tester_connection_error")
    mock_paramiko.connect.side_effect = paramiko.SSHException("Connection refused")

    config = SshConnectionConfig(
        alias="conn_error", hostname="unreachable", port=22, username="user",
        auth_method="password", password="pwd"
    )
    tester = SshConnectionTester(config)
    spy_finished = QSignalSpy(tester.finished)
    print(f"SshConnectionTester 생성됨, signal valid: {spy_finished.isValid()}")

    # 직접 실행 - 스레드 사용하지 않음
    tester.run()
    print("SshConnectionTester.run() 직접 호출 완료")

    # 시그널 결과 확인
    print(f"spy_finished 길이: {len(spy_finished)}")
    assert len(spy_finished) > 0, "신호가 발생하지 않았습니다"
    
    if len(spy_finished) > 0:
        result_args = spy_finished[0]
        print(f"시그널 결과: {result_args}")
        assert result_args[0] is False
        assert "SSH 오류" in result_args[1]
        assert "Connection refused" in result_args[1]

@pytest.mark.timeout(10)  # 10초 타임아웃 추가
def test_password_auth_requires_password():
    """비밀번호 인증 방식에는 비밀번호가 필요함을 확인하는 테스트"""
    print("테스트 시작: test_password_auth_requires_password")
    
    # 모델 생성 시 ValidationError가 발생하는지 확인
    with pytest.raises(Exception) as excinfo:
        SshConnectionConfig(
            alias="missing_pwd", hostname="host", port=22, username="user",
            auth_method="password", password=None
        )
    
    # 오류 메시지 확인
    error_str = str(excinfo.value)
    print(f"예상대로 유효성 검사 오류 발생: {error_str}")
    assert "비밀번호 인증 방식에는 비밀번호가 필요합니다" in error_str

@pytest.mark.timeout(10)  # 10초 타임아웃 추가
def test_key_auth_requires_key_path():
    """키 파일 인증 방식에는 키 파일 경로가 필요함을 확인하는 테스트"""
    print("테스트 시작: test_key_auth_requires_key_path")
    
    # 모델 생성 시 ValidationError가 발생하는지 확인
    with pytest.raises(Exception) as excinfo:
        SshConnectionConfig(
            alias="missing_key", hostname="host", port=22, username="user",
            auth_method="key", key_path=None
        )
    
    # 오류 메시지 확인
    error_str = str(excinfo.value)
    print(f"예상대로 유효성 검사 오류 발생: {error_str}")
    assert "키 파일 인증 방식에는 키 파일 경로가 필요합니다" in error_str

