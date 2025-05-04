import asyncio
import asyncssh
import os
import sys
import logging
from dotenv import load_dotenv
from typing import Optional, List

# --- 로깅 설정 ---
# 로그 레벨을 INFO로 설정하고, 터미널(stdout)에 로그 메시지를 출력합니다.
# 로그 형식은 타임스탬프, 로그 레벨, 메시지를 포함합니다.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)] # 로그가 stdout으로 가도록 명시
)
logger = logging.getLogger(__name__)

async def list_remote_home_directory(
    host: str,
    port: int,
    username: str,
    password: Optional[str] = None,
    # client_keys: Optional[List[str]] = None # 키 인증을 사용할 경우 주석 해제
) -> None:
    """
    AsyncSSH를 사용하여 SSH 서버에 연결하고 홈 디렉토리 내용을 나열합니다.

    Args:
        host: SSH 서버의 호스트 이름 또는 IP 주소.
        port: SSH 서버의 포트 번호.
        username: 인증에 사용할 사용자 이름.
        password: 인증에 사용할 비밀번호 (비밀번호 인증 시). 키 기반 인증 등 다른 방법을 사용하는 경우 None으로 설정합니다.
        # client_keys: 키 인증에 사용할 클라이언트 키 파일 경로 리스트.
    """
    logger.info(f"Attempting to connect to {username}@{host}:{port}...")
    # 경고: known_hosts=None은 호스트 키 검증을 비활성화하여 보안 위험을 초래할 수 있습니다.
    # 이 스크립트는 독립 실행 및 테스트 편의를 위해 검증을 비활성화했지만,
    # 실제 운영 환경에서는 known_hosts 파일 경로를 지정하여 호스트 키를 검증하는 것이 보안상 중요합니다.
    conn_options = asyncssh.SSHClientConnectionOptions(
        known_hosts=None # 호스트 키 검증 비활성화 (보안 주의!)
    )
    try:
        # asyncssh.connect를 사용하여 비동기적으로 SSH 연결을 설정합니다.
        # password 인자만 제공하면 비밀번호 인증을 시도합니다.
        async with asyncssh.connect(
            host,
            port=port,
            username=username,
            password=password,
            options=conn_options
            # client_keys=client_keys, # 키 인증 사용 시 주석 해제 및 password=None 설정
        ) as conn:
            logger.info("Connection successful. Listing home directory contents (~/) ...")
            # 원격 서버의 홈 디렉토리에서 'ls -F ~' 명령을 실행합니다.
            # '-F' 옵션은 파일 유형 표시자(예: 디렉토리 뒤 '/')를 추가하여 가독성을 높입니다.
            # check=True는 명령 실행 실패(non-zero exit status) 시 ProcessError를 발생시킵니다.
            result = await conn.run('ls -F ~', check=True)

            # 터미널에 결과 출력
            print("\n" + "="*40)
            print(f" SSH Home Directory Listing for '{username}@{host}' ")
            print("="*40)
            if result.stdout:
                print("Directory Contents (~/):")
                # stdout 결과를 줄 단위로 분리하고 들여쓰기하여 출력합니다.
                for line in result.stdout.strip().splitlines():
                    print(f"  {line}")
            else:
                 # ls 명령이 출력을 생성하지 않은 경우 (예: 빈 디렉토리)
                 print("  (Directory seems empty or 'ls -F ~' produced no output)")

            # stderr 출력이 있는 경우 경고 로그로 기록합니다.
            if result.stderr:
                logger.warning("Stderr output from 'ls -F ~' command:")
                for line in result.stderr.strip().splitlines():
                    logger.warning(f"  [remote stderr] {line}")

            print("="*40 + "\n")

    except asyncssh.ProcessError as e:
        # 원격 명령 실행 실패 시 상세 정보 로깅 및 사용자 알림
        logger.error(f"Failed to execute command on remote server: {e.reason}")
        logger.error(f"Exit status: {e.exit_status}")
        # stdout/stderr 내용을 로그에 포함하여 디버깅 지원
        stdout_info = f"Stdout: {e.stdout.strip()}" if e.stdout else "No stdout."
        stderr_info = f"Stderr: {e.stderr.strip()}" if e.stderr else "No stderr."
        logger.error(f"{stdout_info}")
        logger.error(f"{stderr_info}")
        print(f"\nError executing 'ls -F ~': Command failed on server. Check logs for details.\n")
    except asyncssh.PermissionDenied as e:
        # 인증 실패 시 사용자에게 명확한 메시지 제공
        logger.error(f"Authentication failed for user '{username}' at {host}:{port}: Permission denied. Please check credentials in .env file.")
        print(f"\nAuthentication failed: {e.reason}. Check username/password in .env.\n")
    except asyncssh.ConnectionLost as e:
        # 연결 유실 시 정보 로깅 및 사용자 알림
        logger.error(f"Connection lost to {host}:{port}: {e.reason}")
        print(f"\nConnection lost: {e.reason}\n")
    except asyncssh.HostKeyNotVerifiable as e:
         # 호스트 키 검증 실패 시 처리 (known_hosts=None 사용 시 이론상 발생하지 않으나 방어적 코딩)
         logger.error(f"Host key verification failed (should be disabled with known_hosts=None!): {e.reason}")
         print(f"\nHost key error: {e.reason}. This is unexpected with current settings.\n")
    except asyncssh.Error as e:
        # 기타 AsyncSSH 관련 에러 처리 (라이브러리 자체 에러)
        logger.error(f"An SSH error occurred connecting to {host}:{port}: {type(e).__name__} - {e.reason} (Code: {e.code})")
        print(f"\nSSH Error: {e.reason}\n")
    except OSError as e:
        # 네트워크 또는 OS 수준의 연결 에러 처리 (예: DNS 조회 실패, 연결 거부)
        logger.error(f"Network or OS error connecting to {host}:{port}: {e}")
        print(f"\nNetwork/OS Error: {e}\n")
    except Exception as e:
        # 예상치 못한 모든 에러 처리 (최후의 방어선)
        logger.exception(f"An unexpected error occurred during SSH operation to {host}:{port}: {e}")
        print(f"\nUnexpected Error: {e}\n")


async def main():
    """
    설정 로드 및 SSH 디렉토리 리스팅 실행을 위한 메인 비동기 함수.
    """
    # 스크립트 파일이 위치한 디렉토리를 기준으로 .env 파일 경로를 설정합니다.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')

    # .env 파일 존재 여부 확인 및 로드
    if os.path.exists(env_path):
        # override=True 설정은 시스템 환경 변수보다 .env 파일의 변수를 우선 적용합니다.
        load_dotenv(dotenv_path=env_path, override=True)
        logger.info(f"Loaded environment variables from: {env_path}")
    else:
        # .env 파일이 없으면 에러 로깅 후 종료
        logger.error(f".env file not found at: {env_path}. Cannot proceed without SSH configuration.")
        sys.exit(1)

    # --- 환경 변수에서 SSH 연결 파라미터 가져오기 ---
    ssh_host = os.getenv("SSH_HOST")
    ssh_port_str = os.getenv("SSH_PORT")
    ssh_username = os.getenv("SSH_USERNAME")
    ssh_auth_type = os.getenv("SSH_AUTH_TYPE", "password").lower() # 기본 인증 방식은 'password'
    ssh_password = os.getenv("SSH_PASSWORD")
    # ssh_key_path = os.getenv("SSH_KEY_PATH") # 키 인증 필요 시 .env 파일에 추가

    # --- 필수 파라미터 유효성 검사 ---
    # 필수 변수들이 .env 파일에 정의되어 있는지 확인합니다.
    missing_vars = []
    if not ssh_host: missing_vars.append("SSH_HOST")
    if not ssh_port_str: missing_vars.append("SSH_PORT")
    if not ssh_username: missing_vars.append("SSH_USERNAME")

    if missing_vars:
        logger.error(f"Missing required SSH environment variables in .env: {', '.join(missing_vars)}")
        sys.exit(1) # 필수 변수 누락 시 종료

    # --- 포트 번호 유효성 검사 (정수 및 범위 확인) ---
    try:
        ssh_port = int(ssh_port_str)
        if not (0 < ssh_port < 65536): # 포트 번호는 1-65535 범위여야 함
             raise ValueError("Port number out of valid range (1-65535)")
    except ValueError as e:
        logger.error(f"Invalid SSH_PORT value '{ssh_port_str}'. It must be an integer between 1 and 65535. Error: {e}")
        sys.exit(1) # 유효하지 않은 포트 번호 시 종료

    # --- 인증 파라미터 유효성 검사 및 설정 ---
    password_to_use = None
    # client_keys_to_use = None # 키 인증 필요 시 주석 해제

    if ssh_auth_type == "password":
        if not ssh_password:
            # 비밀번호 인증 방식인데 비밀번호가 .env에 없는 경우 에러 처리
            logger.error("SSH_AUTH_TYPE is set to 'password' but SSH_PASSWORD is not defined in the .env file.")
            sys.exit(1)
        password_to_use = ssh_password
        logger.info("Authentication method set to: password")
    # elif ssh_auth_type == "key": # 키 인증 로직 (현재 비활성화)
    #     if not ssh_key_path:
    #         logger.error("SSH_AUTH_TYPE is 'key' but SSH_KEY_PATH is not set in .env.")
    #         sys.exit(1)
    #     # .env 파일 기준 상대 경로 또는 절대 경로 처리
    #     key_full_path = os.path.abspath(os.path.join(script_dir, ssh_key_path))
    #     if not os.path.exists(key_full_path):
    #          logger.error(f"SSH key file specified by SSH_KEY_PATH does not exist: '{key_full_path}'")
    #          sys.exit(1)
    #     client_keys_to_use = [key_full_path]
    #     logger.info(f"Authentication method set to: key (Using key: {key_full_path})")
    else:
        # 지원하지 않는 인증 방식 처리
        logger.error(f"Unsupported SSH_AUTH_TYPE specified in .env: '{ssh_auth_type}'. Currently supported: 'password'.") # 'key' 지원 시 메시지 수정
        sys.exit(1)

    # --- SSH 디렉토리 리스팅 함수 실행 ---
    # 추출 및 검증된 파라미터를 사용하여 원격 디렉토리 리스팅 함수 호출
    await list_remote_home_directory(
        host=ssh_host,
        port=ssh_port,
        username=ssh_username,
        password=password_to_use,
        # client_keys=client_keys_to_use # 키 인증 필요 시 주석 해제
    )

if __name__ == "__main__":
    # 스크립트가 직접 실행될 때 asyncio 이벤트 루프를 시작하고 main 코루틴 실행
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # 사용자가 Ctrl+C로 실행을 중단했을 때 정보 메시지 출력
        logger.info("Script execution interrupted by user (Ctrl+C).")
        sys.exit(0)
    except Exception as e:
        # main 실행 중 예상치 못한 최상위 레벨 오류 발생 시 로깅 및 종료
        # 개발/디버깅 시 유용
        logger.exception(f"A critical error occurred during script execution: {e}")
        sys.exit(1)


