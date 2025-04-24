# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# src 디렉토리를 sys.path에 추가 (빌드 시점에 필요)
src_dir = os.path.join(os.path.dirname(__file__), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 리소스 경로 설정 함수 (빌드 시점용)
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

a = Analysis(
    # 엔트리 포인트 변경: main.py 또는 src/app.py
    # main.py를 사용하는 것이 일반적
    ['main.py'],
    pathex=[src_dir], # src 디렉토리 포함
    binaries=[],
    datas=[
        # 리소스 경로 수정 (resource_path 함수 사용 또는 상대 경로 유지)
        (resource_path('resources/rubber_duck.ico'), 'resources'),
        (resource_path('resources/prompts'), 'resources/prompts'),
        (resource_path('resources/status'), 'resources/status'), # 상태 디렉토리 추가
        (resource_path('src/config.yml'), 'src'), # 설정 파일 추가
        # 필요한 경우 .env 파일도 포함 (보안 고려)
        # (resource_path('.env'), '.')
    ],
    # hiddenimports는 유지 또는 필요시 추가/삭제
    hiddenimports=[
        'tiktoken',
        'tiktoken_ext',
        'tiktoken_ext.openai_public',
        'pydantic', # pydantic 추가
        'yaml',     # PyYAML 추가
        'pkg_resources', # PyInstaller에서 종종 필요
        'dotenv',   # python-dotenv 추가
        # PyQt5 관련 hidden import는 보통 자동으로 처리됨
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
    [], # a.binaries는 아래 COLLECT에서 처리되도록 비움
    # a.datas는 아래 COLLECT에서 처리되도록 비움
    # [],
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
    # 아이콘 경로 수정
    icon=[resource_path('resources/rubber_duck.ico')],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas, # datas를 COLLECT로 이동
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DuckPrompt',
)
