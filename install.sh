#!/usr/bin/env bash
# Installe claude-chat-bar comme status line de Claude Code.
set -euo pipefail

TARGET_DIR="$HOME/.claude/claude-chat-bar"
SETTINGS="$HOME/.claude/settings.json"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v python3 >/dev/null || { echo "python3 est requis." >&2; exit 1; }

mkdir -p "$TARGET_DIR"
install -m 755 "$SRC_DIR/statusline.py" "$TARGET_DIR/statusline.py"

[ -f "$SETTINGS" ] && cp "$SETTINGS" "$SETTINGS.bak"

python3 - "$SETTINGS" "$TARGET_DIR/statusline.py" <<'PY'
import json, os, sys
path, script = sys.argv[1], sys.argv[2]
settings = {}
if os.path.exists(path):
    with open(path) as f:
        settings = json.load(f)
settings["statusLine"] = {
    "type": "command",
    "command": f"python3 {script}",
    "padding": 0,
    "refreshInterval": 2,
}
with open(path, "w") as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
    f.write("\n")
PY

echo "claude-chat-bar installé dans $TARGET_DIR"
echo "Réglage ajouté dans $SETTINGS (sauvegarde : $SETTINGS.bak)"
