#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

pick_python() {
  if command -v python3.12 >/dev/null 2>&1; then
    printf '%s\n' "python3.12"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    local version
    version="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    if [[ "${version}" == "3.12" ]]; then
      printf '%s\n' "python3"
      return 0
    fi
  fi

  printf '%s\n' "X4 Wallpaper Maker requires Python 3.12. Install python3.12 and run ./run-app.sh again." >&2
  return 1
}

python_cmd="$(pick_python)"

needs_install=0
if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  needs_install=1
else
  venv_version="$("${VENV_DIR}/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  if [[ "${venv_version}" != "3.12" ]]; then
    printf '%s\n' "Rebuilding .venv with Python 3.12 to match the project requirement."
    rm -rf "${VENV_DIR}"
    needs_install=1
  fi
fi

if [[ "${needs_install}" -eq 1 ]]; then
  "${python_cmd}" -m venv "${VENV_DIR}"
  "${VENV_DIR}/bin/python" -m pip install --upgrade pip
  "${VENV_DIR}/bin/python" -m pip install -e "${ROOT_DIR}"
fi

exec "${VENV_DIR}/bin/x4-wallpaper-maker"
