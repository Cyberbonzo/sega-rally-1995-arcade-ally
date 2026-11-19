#!/bin/bash
export STEAM_COMPAT_CLIENT_INSTALL_PATH="$HOME/.steam/root"
export STEAM_COMPAT_DATA_PATH="$HOME/Games/.prefixes/SegaRally"
cd "$(dirname "$0")" || exit 1
mkdir -p "$STEAM_COMPAT_DATA_PATH" logs
python3 ./pausa.py >>logs/pausa.log 2>&1 &
watcher=$!
trap 'kill "$watcher" 2>/dev/null || true' EXIT
"$HOME/.steam/root/compatibilitytools.d/GE-Proton11-5/proton" run ./segarally.exe "$@"
