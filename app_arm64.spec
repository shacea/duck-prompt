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

block_cipher = None

a = Analysis(
    # 엔트리 포인트 변경: main.py 또는 src/app.py
    ['main.py'],
    pathex=[src_dir], # src 디렉토리 포함
    binaries=[],
    datas=[
        # 리소스 경로 수정
        (resource_path('resources/rubber_duck.ico'), 'resources'),
        (resource_path('resources/prompts'), 'resources/prompts'),
        (resource_path('resources/status'), 'resources/status'), # 상태 디렉토리 추가
        (resource_path('src/config.yml'), 'src'), # 설정 파일 추가
        # (resource_path('.env'), '.') # .env 포함 여부 결정
    ],
    # hiddenimports 수정
    hiddenimports=[
        'tiktoken',
        'tiktoken_ext',
        'tiktoken_ext.openai_public',
        'pydantic',
        'yaml',
        'pkg_resources',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [], # a.binaries는 아래 COLLECT에서 처리
    # a.zipfiles, # zipfiles는 보통 필요 없음
    # a.datas, # datas는 아래 COLLECT에서 처리
    # [],
    name='DuckPrompt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # GUI 애플리케이션
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
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
