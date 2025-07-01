#!/usr/bin/env bash
# gotoAppImage  ── Build a fully-self-contained Serpent.AI AppImage.
#
# This script reproduces the manual steps described in the user manual:
#  * spins up a Python venv in /opt/serpent
#  * installs SerpentAI[full] into it
#  * assembles an AppDir containing the venv + launcher
#  * runs linuxdeploy (with python plugin) + appimagetool to generate
#    SerpentAI-<arch>.AppImage in the current working directory.
#
# Requirements on the build host (manylinux2014 or Ubuntu-20.04 recommended):
#  * bash, wget, patchelf, desktop-file-utils
#  * linuxdeploy AppImage (will be auto-downloaded if missing)
#  * appimagetool AppImage (auto-downloaded)
#
# Usage:
#     chmod +x gotoAppImage.sh
#     ./gotoAppImage.sh
#
set -euo pipefail

VERSION="$(date +%Y.%m.%d)"
APP=SerpentAI
APPDIR="/tmp/${APP}.AppDir"
PY_ROOT="/opt/serpent"
PY_BIN="${PY_ROOT}/bin/python"
ARCH=$(uname -m)
OUTPUT="${APP}-${VERSION}-${ARCH}.AppImage"

# ----------------------------------------------------------------------------
# 0. Fetch helpers (linuxdeploy & appimagetool)
# ----------------------------------------------------------------------------
LINUXDEPLOY=linuxdeploy
APPIMAGETOOL=appimagetool

if ! command -v ${LINUXDEPLOY} &>/dev/null; then
  echo "Downloading linuxdeploy…" >&2
  wget -qO linuxdeploy https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
  chmod +x linuxdeploy
  LINUXDEPLOY="$(pwd)/linuxdeploy"
fi

if ! command -v ${APPIMAGETOOL} &>/dev/null; then
  echo "Downloading appimagetool…" >&2
  wget -qO appimagetool https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x appimagetool
  APPIMAGETOOL="$(pwd)/appimagetool"
fi

# ----------------------------------------------------------------------------
# 1. Create venv & install Serpent.AI
# ----------------------------------------------------------------------------
if [[ ! -x "${PY_BIN}" ]]; then
  echo "Creating Python virtual environment in ${PY_ROOT}" >&2
  python3 -m venv "${PY_ROOT}"
  "${PY_BIN}" -m pip install --upgrade pip wheel
  "${PY_BIN}" -m pip install .[full] streamlit linuxdeploy-plugin-python
fi

# ----------------------------------------------------------------------------
# 2. Populate AppDir
# ----------------------------------------------------------------------------
rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin" "${APPDIR}/usr/share/applications" \
         "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

# Copy venv into AppDir
cp -r "${PY_ROOT}" "${APPDIR}/usr/serpent-venv"

# Wrapper launcher
cat > "${APPDIR}/usr/bin/serpent" <<'SH'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
VENV="$HERE/../serpent-venv"
exec "$VENV/bin/python" -m serpent.cli "$@"
SH
chmod +x "${APPDIR}/usr/bin/serpent"

# Desktop entry
cat > "${APPDIR}/usr/share/applications/serpent-ai.desktop" <<'DESK'
[Desktop Entry]
Name=Serpent.AI Dashboard
Exec=serpent gui
Icon=serpent
Type=Application
Categories=Game;Science;
DESK

# Icon (fallback to built-in logo)
ICON_SRC=$(python - <<'PY'
import importlib.resources as res, sys, pathlib
try:
    from serpent import dashboard
    p = res.files(dashboard)/'serpent.png'
    print(p)
except Exception:
    sys.exit(1)
PY
)
if [[ -f "$ICON_SRC" ]]; then
  cp "$ICON_SRC" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/serpent.png"
fi

# ----------------------------------------------------------------------------
# 3. Run linuxdeploy + plugin-python
# ----------------------------------------------------------------------------
"${LINUXDEPLOY}" --appdir "${APPDIR}" \
              --desktop-file "${APPDIR}/usr/share/applications/serpent-ai.desktop" \
              --icon-file "${APPDIR}/usr/share/icons/hicolor/256x256/apps/serpent.png" \
              --output appimage \
              --plugin python

# linuxdeploy outputs to current dir
mv *.AppImage "${OUTPUT}"

# Generate zsync + embed update information for AppImageUpdate
UPDATE_URL="gh-releases-zsync|SerpentAI|SerpentAI|latest|SerpentAI-*-${ARCH}.AppImage.zsync"

# Re-run appimagetool with update info (requires appimagetool)
"${APPIMAGETOOL}" --updateinformation="${UPDATE_URL}" "${APPDIR}" "${OUTPUT}" > /dev/null 2>&1 || true

chmod +x "${OUTPUT}"
echo "\n✅  Built ${OUTPUT}"