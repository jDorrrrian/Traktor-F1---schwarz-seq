#!/bin/bash
# Install F1DrumSequencer into Ableton Live's MIDI Remote Scripts folder.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE="$SCRIPT_DIR/F1DrumSequencer"

LIVE_APP="/Applications/Ableton Live 12 Suite.app"
LIVE_SCRIPTS="$LIVE_APP/Contents/App-Resources/MIDI Remote Scripts"
USER_SCRIPTS="$HOME/Music/Ableton/User Library/Remote Scripts"

if [[ ! -d "$SOURCE" ]]; then
  echo "Error: F1DrumSequencer folder not found at $SOURCE"
  exit 1
fi

install_to() {
  local dest="$1/F1DrumSequencer"
  echo "Installing to $dest"
  rm -rf "$dest"
  mkdir -p "$(dirname "$dest")"
  cp -R "$SOURCE" "$dest"
  rm -rf "$dest/__pycache__"
  echo "Done."
}

if [[ -d "$LIVE_SCRIPTS" ]]; then
  install_to "$LIVE_SCRIPTS"
else
  echo "Warning: Live scripts folder not found at $LIVE_SCRIPTS"
fi

if [[ -d "$HOME/Music/Ableton/User Library" ]] || mkdir -p "$USER_SCRIPTS"; then
  install_to "$USER_SCRIPTS"
fi

echo ""
echo "Restart Ableton Live completely, then select F1DrumSequencer in Preferences → MIDI."
