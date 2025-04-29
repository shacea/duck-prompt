import sys
import os

# src 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# src/app.py의 메인 함수 실행
if __name__ == '__main__':
    # app 모듈을 여기서 임포트하여 순환 참조 방지 가능성 고려
    from app import main
    main()
