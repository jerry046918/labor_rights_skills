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

# Required models — must match process.py (VAD/ASR/SPK/PUNC)
declare -a MODELS=(
  "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
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
  # ffprobe is OPTIONAL: process.py has a librosa fallback that handles
  # duration detection when ffprobe is not on PATH (common in Git Bash
  # on Windows). Install via --with-ffmpeg only if you want faster probing.
  if command -v ffprobe &> /dev/null; then
    echo "ffprobe: OK (optional)"
    return 0
  fi
  echo "ffprobe: not on PATH (OK — process.py falls back to librosa)"
  return 0
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
    # modelscope nests under the org id (e.g., iic/), check both layouts
    if [[ ! -d "$MODELS_DIR/$name" && ! -d "$MODELS_DIR/iic/$name" ]]; then
      return 1
    fi
  done
  return 0
}

do_check() {
  echo "=== Environment Check ==="
  check_python || return 1
  check_ffprobe
  if check_venv; then
    echo "venv: OK"
  else
    echo "venv: MISSING"
    return 1
  fi
  if check_models; then
    echo "models: OK ($(echo "${MODELS[@]}" | wc -w) models)"
  else
    echo "models: MISSING (expected ${#MODELS[@]} models)"
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

  echo "Installing FunASR deps (skip editdistance — only needed for CER/WER eval, not inference)..."
  pip install --index-url "$PIP_INDEX" \
    "scipy>=1.4.1" librosa "soundfile>=0.12.1" numpy "PyYAML>=5.1.2" \
    tqdm requests "omegaconf>=2.0" "hydra-core>=1.3.2" modelscope \
    huggingface_hub safetensors transformers tiktoken sentencepiece \
    "kaldiio>=2.17.0" jieba jamo jaconv umap_learn torch_complex tensorboardX oss2 \
    "edge-tts>=6.1.0" "pytest>=7.0.0"

  echo "Installing FunASR itself with --no-deps..."
  pip install --no-deps --index-url "$PIP_INDEX" "funasr>=1.3.0"

  echo "Verifying FunASR import..."
  python -c "from funasr import AutoModel; print('FunASR import OK')" \
    || { echo "ERROR: FunASR import failed"; return 1; }
}

download_models() {
  echo "Downloading models from ModelScope..."
  # Convert Git Bash path to Windows path so Python on Windows understands it
  local win_models_dir
  if command -v cygpath &> /dev/null; then
    win_models_dir=$(cygpath -w "$MODELS_DIR")
  else
    win_models_dir="$MODELS_DIR"
  fi
  MODELS_DIR_WIN="$win_models_dir" python -c "
import os
from modelscope.hub.snapshot_download import snapshot_download
cache_dir = os.environ['MODELS_DIR_WIN']
# Must match MODELS array at top of this file and process.py constants
models = [
  'iic/speech_fsmn_vad_zh-cn-16k-common-pytorch',
  'iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch',
  'iic/speech_campplus_sv_zh-cn_16k-common',
  'iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727',
]
for m in models:
  print(f'Downloading {m}...')
  snapshot_download(m, cache_dir=cache_dir)
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
