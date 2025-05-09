
# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path # pathlib 사용
# from PyInstaller.utils.hooks import collect_all # collect_all 더 이상 사용 안 함

# src 디렉토리를 sys.path에 추가 (빌드 시점에 필요)
# __file__ 대신 Path.cwd() 사용 (PyInstaller 실행 시 현재 작업 디렉토리가 spec 파일 위치임)
spec_dir = Path.cwd()
src_dir = spec_dir / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# 리소스 경로 설정 함수 (빌드 시점용)
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    # PyInstaller 번들 내부 경로 또는 개발 환경의 프로젝트 루트 경로
    base_path = Path(getattr(sys, '_MEIPASS', spec_dir))
    return str(base_path / relative_path)

# collect_all 호출 제거, 기본 datas만 정의
# 아이콘 복사 방식 변경: resources/icons 폴더 전체를 번들 내 resources/icons 로 복사
datas = [
    (resource_path('resources/icons'), 'resources/icons'), # 아이콘 폴더 복사
    (resource_path('resources/prompts'), 'resources/prompts'),
    (resource_path('resources/status'), 'resources/status'),
    (resource_path('resources/fonts/malgun.ttf'), 'resources/fonts'), # 폰트 파일 추가
    (resource_path('src/config.yml'), 'src'),
]
binaries = [] # 필요한 바이너리는 PyInstaller가 자동으로 찾도록 함


a = Analysis(
    # 엔트리 포인트: main.py
    [str(spec_dir / 'main.py')],
    pathex=[str(src_dir)], # src 디렉토리 포함
    binaries=binaries, # 기본값 사용
    datas=datas,       # 리소스 및 폰트 포함
    hiddenimports=[
        'pkg_resources',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [], # binaries는 Analysis에서 처리
    name='DuckPrompt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # GUI 애플리케이션이므로 False 유지
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='amd64',
    codesign_identity=None,
    entitlements_file=None,
    # 실행 파일 자체의 아이콘 설정 (경로 수정 불필요)
    icon=[resource_path('resources/icons/rubber_duck.ico')],
)
coll = COLLECT(
    exe,
    a.binaries, # Analysis에서 정의된 binaries 사용
    a.datas,    # Analysis에서 정의된 datas 사용
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DuckPrompt',
)
