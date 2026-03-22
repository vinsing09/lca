# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# SPECPATH is the directory containing this spec file (build/).
# The repo root is one level up.
REPO_ROOT = str(Path(SPECPATH).parent)

a = Analysis(
    [str(Path(SPECPATH) / '_lca_main.py')],
    pathex=[REPO_ROOT],
    binaries=[],
    datas=[],
    hiddenimports=[
        'typer', 'typer.main', 'click', 'click.exceptions',
        'rich', 'rich.console', 'rich.panel', 'rich.progress', 'rich.rule',
        'rich.text', 'rich.syntax', 'rich.table', 'rich.markup', 'rich.theme',
        'rich.style', 'rich.color', 'rich.segment', 'rich.live', 'rich.spinner',
        'httpx', 'httpx._client', 'httpx._transports.default',
        'httpcore', 'certifi',
        'psutil',
        'tree_sitter', 'tree_sitter_python', 'tree_sitter_javascript', 'tree_sitter_go',
        'lca.commands.explain', 'lca.commands.review', 'lca.commands.edit',
        'lca.runtime.hardware',
        'lca.context.reader', 'lca.context.limiter', 'lca.context.extractor',
        'lca.llm.client', 'lca.llm.prompts',
        'lca.output.stream', 'lca.output.diff',
        'lca.config',
        'setuptools._vendor.jaraco.text',
        'setuptools._vendor.jaraco.functools',
        'setuptools._vendor.jaraco.context',
    ],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy', 'PIL', 'cv2',
        'torch', 'tensorflow', 'IPython', 'jupyter', 'pytest',
    ],
    hookspath=[str(Path(SPECPATH) / 'hooks')],
    hooksconfig={},
    runtime_hooks=[str(Path(SPECPATH) / 'hooks' / 'rthook_jaraco.py')],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='lca',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
