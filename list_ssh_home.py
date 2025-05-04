import asyncio
import os
import sys
import logging
from dotenv import load_dotenv
from typing import Union, List

# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 프로젝트 루트 및 src 경로 설정 ---
# 이 스크립트가 프로젝트 루트에 있다고 가정
project_root = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_root, "src")

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
    logger.info(f"Added '{src_dir}' to sys.path.")

# --- 필요한 서비스 및 유틸리티 임포트 ---
try:
    from core.services.db_service import DbService
    from core.services.ssh_config_service import SshConfigService
    from core.utils.ssh_utils import connect_and_list_home_dir
except ImportError as e:
    logger.critical(f"Failed to import necessary modules from 'src'. Ensure '{src_dir}' is correct and contains the required modules: {e}")
    sys.exit(1)
except Exception as e:
    logger.critical(f"An unexpected error occurred during module import: {e}")
    sys.exit(1)


async def main():
    """
    Main asynchronous function to connect to SSH and list home directory.
    """
    # --- .env 파일 로드 ---
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path, override=True)
        logger.info(f"Loaded environment variables from: {env_path}")
    else:
        logger.warning(f".env file not found at: {env_path}. Cannot proceed without SSH configuration.")
        return

    # --- 환경 변수에서 SSH 별칭 가져오기 ---
    ssh_alias = os.getenv("SSH_ALIAS")
    if not ssh_alias:
        logger.error("SSH_ALIAS not found in environment variables (.env). Please define it.")
        return

    db_service = None
    try:
        # --- 서비스 초기화 ---
        logger.info("Initializing services...")
        db_service = DbService()
        ssh_config_service = SshConfigService(db_service)
        logger.info("Services initialized.")

        # --- SSH 설정 가져오기 ---
        logger.info(f"Retrieving SSH configuration for alias: '{ssh_alias}'...")
        ssh_config = ssh_config_service.get_connection(ssh_alias)

        if not ssh_config:
            logger.error(f"SSH configuration for alias '{ssh_alias}' not found in the database.")
            return

        logger.info(f"Found SSH config: Host={ssh_config.host}, Port={ssh_config.port}, User={ssh_config.username}, Auth={ssh_config.auth_type}")

        # --- SSH 연결 및 홈 디렉토리 리스팅 ---
        logger.info("Connecting to SSH server and listing home directory...")
        success, result = await connect_and_list_home_dir(ssh_config)

        # --- 결과 출력 ---
        print("\n" + "="*30)
        print(f" SSH Home Directory Listing Results for '{ssh_alias}' ({ssh_config.host}) ")
        print("="*30)
        if success:
            print("Connection and listing successful.")
            print("Directory Contents (~/):")
            if isinstance(result, list):
                if result:
                    for item in result:
                        print(f"  - {item}")
                else:
                    print("  (Directory is empty)")
            else:
                # 이 경우는 발생하지 않아야 하지만 방어적으로 처리
                print(f"  Unexpected result format: {result}")
        else:
            print(f"Failed to connect or list directory.")
            print(f"Error: {result}")
        print("="*30 + "\n")

    except ConnectionError as e:
         logger.error(f"Database connection failed: {e}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
    finally:
        # --- 서비스 연결 해제 ---
        if db_service:
            try:
                db_service.disconnect()
                logger.info("Database connection closed.")
            except Exception as e:
                logger.error(f"Error disconnecting database: {e}")

if __name__ == "__main__":
    # 비동기 main 함수 실행
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Script interrupted by user.")
        sys.exit(0)

        