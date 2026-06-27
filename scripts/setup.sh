#!/usr/bin/env bash
# setup.sh - FunASR environment setup for labor_rights_advisor skill
# Usage:
#   ./setup.sh --check                 # check if environment is ready
#   ./setup.sh --install               # install FunASR + models (default mirror: China)
#   ./setup.sh --install --with-ffmpeg # also download ffmpeg static binary
#   ./setup.sh --redownload-models     # re-download model files only

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SKILL_DIR/.venv-funasr"
MODELS_DIR="$SKILL_DIR/models"

# China mirrors
PIP_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"
TORCH_INDEX="https://download.pytorch.org/whl/cpu"
MODELSCOPE_ENDPOINT="https://www.modelscope.cn"

# Required models
declare -a MODELS=(
  "iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
  "iic/speech_campplus_sv_zh-cn_16k-common"
  "iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727"
)

check_python() {
  if ! command -v python &> /dev/null; then
    echo "ERROR: python not found in PATH"
    echo "Please install Python 3.9+ from https://www.python.org/downloads/"
    return 1
  fi
  local ver
  ver=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  echo "Python: $ver"
}

check_ffprobe() {
  if command -v ffprobe &> /dev/null; then
    echo "ffprobe: OK"
    return 0
  fi
  echo "ffprobe: MISSING (use --with-ffmpeg to install)"
  return 1
}

check_venv() {
  if [[ -d "$VENV_DIR" && -f "$VENV_DIR/Scripts/activate" || -f "$VENV_DIR/bin/activate" ]]; then
    return 0
  fi
  return 1
}

check_models() {
  for model in "${MODELS[@]}"; do
    local name="${model##*/}"
    if [[ ! -d "$MODELS_DIR/$name" ]]; then
      return 1
    fi
  done
  return 0
}

do_check() {
  echo "=== Environment Check ==="
  check_python || return 1
  check_ffprobe || echo "  (warning: ffprobe missing, see --with-ffmpeg)"
  if check_venv; then
    echo "venv: OK"
  else
    echo "venv: MISSING"
    return 1
  fi
  if check_models; then
    echo "models: OK"
  else
    echo "models: MISSING"
    return 1
  fi
  echo "=== Ready ==="
}

create_venv() {
  echo "Creating venv at $VENV_DIR..."
  python -m venv "$VENV_DIR"
  # Activate (cross-platform)
  if [[ -f "$VENV_DIR/Scripts/activate" ]]; then
    source "$VENV_DIR/Scripts/activate"
  else
    source "$VENV_DIR/bin/activate"
  fi
}

install_deps() {
  echo "Installing PyTorch (CPU) from China mirror..."
  pip install --index-url "$TORCH_INDEX" torch torchaudio
  echo "Installing FunASR and deps from Tsinghua mirror..."
  pip install --index-url "$PIP_INDEX" -r "$SCRIPT_DIR/requirements.txt"
}

download_models() {
  echo "Downloading models from ModelScope..."
  python -c "
from modelscope.hub.snapshot_download import snapshot_download
models = [
  'iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch',
  'iic/speech_campplus_sv_zh-cn_16k-common',
  'iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727',
]
for m in models:
  print(f'Downloading {m}...')
  snapshot_download(m, cache_dir='$MODELS_DIR')
print('All models downloaded.')
"
}

download_ffmpeg() {
  echo "Downloading ffmpeg static binary..."
  local ff_url="https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
  local ff_zip="$SKILL_DIR/ffmpeg.zip"
  local ff_dir="$SKILL_DIR/ffmpeg"
  curl -L "$ff_url" -o "$ff_zip"
  unzip -q "$ff_zip" -d "$ff_dir"
  rm "$ff_zip"
  echo "ffmpeg extracted to $ff_dir"
  echo "Add to PATH: export PATH=\"$ff_dir/bin:\$PATH\""
}

do_install() {
  check_python
  if ! check_venv; then create_venv; fi
  # Activate venv
  if [[ -f "$VENV_DIR/Scripts/activate" ]]; then
    source "$VENV_DIR/Scripts/activate"
  else
    source "$VENV_DIR/bin/activate"
  fi
  install_deps
  download_models
  if [[ "${1:-}" == "--with-ffmpeg" ]]; then
    download_ffmpeg
  fi
  echo "=== Install complete, running check... ==="
  do_check
}

case "${1:-}" in
  --check) do_check ;;
  --install) do_install "${2:-}" ;;
  --redownload-models) download_models ;;
  *) echo "Usage: $0 [--check|--install [--with-ffmpeg]|--redownload-models]"; exit 1 ;;
esac
