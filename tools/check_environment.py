"""설치·설정 변경이나 네트워크 요청 없이 필요한 실행 환경을 확인한다."""

import argparse
import importlib.metadata
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def command_version(name):
    executable = shutil.which(name)
    if executable is None:
        return "없음 (필요한 경우에만 설치 검토)"
    try:
        result = subprocess.run(
            [executable, "--version"], capture_output=True, text=True,
            timeout=3, errors="replace",
        )
        if result.returncode != 0:
            return "확인 불가 (버전 조회 실패)"
        lines = (result.stdout or result.stderr).strip().splitlines()
        return lines[0] if lines else "확인 불가 (버전 응답 없음)"
    except subprocess.TimeoutExpired:
        return "확인 불가 (3초 초과)"
    except OSError as error:
        return "확인 불가 ({})".format(type(error).__name__)


def package_version(name):
    try:
        return importlib.metadata.version(name) + " (설치 정보)"
    except importlib.metadata.PackageNotFoundError:
        return "없음 (필요한 경우에만 설치 검토)"


def check_writable(workspace):
    try:
        # 기존 파일에 손대지 않고 생성·기록·삭제 권한을 함께 확인한다.
        with tempfile.TemporaryFile(dir=workspace) as probe:
            probe.write(b"check")
            probe.flush()
        return "가능 (임시 파일 생성·기록·삭제 확인)", True
    except OSError as error:
        return "확인 실패 ({})".format(type(error).__name__), False


def main():
    parser = argparse.ArgumentParser(
        description="실행 환경 요약. 도구·패키지가 없어도 실패로 처리하지 않습니다."
    )
    parser.add_argument("--workspace", type=Path, default=Path.cwd(),
                        help="쓰기 확인 폴더 (기본: 현재 폴더)")
    parser.add_argument("--package", action="append", default=[], metavar="NAME",
                        help="설치 버전을 확인할 패키지. 여러 번 지정 가능")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    print("Python: {} ({})".format(platform.python_version(), sys.executable))
    print("작업 폴더: {}".format(workspace))
    for name in ("git", "node", "uv"):
        print("{}: {}".format(name, command_version(name)))
    for name in dict.fromkeys(args.package):
        print("패키지 {}: {}".format(name, package_version(name)))
    message, writable = check_writable(workspace)
    print("폴더 쓰기: {}".format(message))
    print("패키지 import·서버 연결·업무 기능은 검사하지 않았습니다.")
    return 0 if writable else 1


if __name__ == "__main__":
    sys.exit(main())
