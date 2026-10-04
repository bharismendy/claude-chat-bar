#!/usr/bin/env python3
"""claude-chat-bar : status line pour Claude Code, avec un chat de compagnie.

Claude Code envoie l'état de la session en JSON sur stdin ; tout ce que ce
script affiche sur stdout devient la barre de statut (une ligne par print).
"""

import json
import os
import sys
import time
from datetime import datetime

PET_NAME = os.environ.get("CLAUDE_PET_NAME", "Mochi")
NO_COLOR = bool(os.environ.get("NO_COLOR"))

# Nombre d'octets lus à la fin du transcript pour deviner l'activité en cours.
TAIL_BYTES = 256 * 1024
# Un sous-agent dont le transcript a bougé depuis moins de N s est considéré actif.
AGENT_ACTIVE_SECONDS = 30
# Au-delà de N s sans activité, le chat s'endort.
SLEEP_AFTER_SECONDS = 5 * 60

RESET = "\033[0m"
COLORS = {
    "dim": "\033[2m",
    "bold": "\033[1m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "orange": "\033[38;5;208m",
}


def c(text, *styles):
    if NO_COLOR or not styles:
        return text
    return "".join(COLORS[s] for s in styles) + text + RESET


def get(data, *path, default=None):
    for key in path:
        if not isinstance(data, dict):
            return default
        data = data.get(key)
    return default if data is None else data


# --------------------------------------------------------------------------
# Lecture du transcript
# --------------------------------------------------------------------------

def read_entries(path, tail_only):
    """Entrées JSONL du transcript principal (hors sous-agents)."""
    try:
        with open(path, "rb") as f:
            if tail_only:
                f.seek(0, os.SEEK_END)
                f.seek(max(0, f.tell() - TAIL_BYTES))
                f.readline()  # ligne probablement tronquée
            raw = f.read()
    except OSError:
        return []
    entries = []
    for line in raw.splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get("type") in ("user", "assistant") and not entry.get("isSidechain"):
            entries.append(entry)
    return entries


def blocks(entry):
    content = get(entry, "message", "content")
    return content if isinstance(content, list) else []


def count_xp(path):
    """Expérience du chat : prompts envoyés + outils utilisés pendant la session."""
    xp = 0
    for entry in read_entries(path, tail_only=False):
        content = get(entry, "message", "content")
        if entry["type"] == "user" and isinstance(content, str):
            xp += 1
        xp += sum(1 for b in blocks(entry) if b.get("type") == "tool_use")
    return xp


def analyse_activity(path):
    """Dernière action dans la conversation et agents lancés en avant-plan."""
    entries = read_entries(path, tail_only=True)
    agent_calls, results = set(), set()
    for entry in entries:
        for b in blocks(entry):
            if b.get("type") == "tool_use" and b.get("name") in ("Agent", "Task"):
                agent_calls.add(b.get("id"))
            elif b.get("type") == "tool_result":
                results.add(b.get("tool_use_id"))

    activity = {"kind": "idle", "tool": None}
    for entry in reversed(entries):
        content = get(entry, "message", "content")
        if entry["type"] == "user" and isinstance(content, str):
            activity = {"kind": "prompt", "tool": None}
            break
        tool_uses = [b for b in blocks(entry) if b.get("type") == "tool_use"]
        tool_results = [b for b in blocks(entry) if b.get("type") == "tool_result"]
        if tool_results:
            if any(b.get("is_error") for b in tool_results):
                activity = {"kind": "error", "tool": None}
            else:
                activity = {"kind": "thinking", "tool": None}
            break
        if tool_uses:
            activity = {"kind": "tool", "tool": tool_uses[-1].get("name")}
            break
        if entry["type"] == "assistant":
            activity = {"kind": "idle", "tool": None}
            break
        if entry["type"] == "user":
            activity = {"kind": "prompt", "tool": None}
            break

    return activity, len(agent_calls - results)


def count_running_agents(transcript_path, pending_foreground):
    """Sous-agents actifs : appels en attente ou transcripts récemment modifiés."""
    base, _ = os.path.splitext(transcript_path)
    folder = os.path.join(base, "subagents")
    recent = 0
    now = time.time()
    try:
        for name in os.listdir(folder):
            if name.endswith(".jsonl"):
                if now - os.path.getmtime(os.path.join(folder, name)) < AGENT_ACTIVE_SECONDS:
                    recent += 1
    except OSError:
        pass
    return max(recent, pending_foreground)


# --------------------------------------------------------------------------
# Le chat
# --------------------------------------------------------------------------

# Chaque humeur : (deux images pour l'animation, légende, couleur)
MOODS = {
    "sleep":    (("(=-ω-=) zZ", "(=-ω-=) Zz"), "dort", "dim"),
    "listen":   (("(=ºωº=)?", "(=ºωº=)!"), "t'écoute", "cyan"),
    "think":    (("(=･ω･=) …", "(=･ω･=)..."), "réfléchit", "blue"),
    "type":     (("(=^･ω･^=)⌨", "(=^･ω･^=)ﾉ⌨"), "tape au clavier", "green"),
    "read":     (("(=◕ω◕=)📖", "(=◔ω◔=)📖"), "lit le code", "green"),
    "write":    (("(=^･ω･^=)✎", "(=^･ω･^=)✐"), "écrit du code", "green"),
    "hunt":     (("(=ↀωↀ=)⌕", "(=ↀωↀ=) ⌕"), "chasse sur le web", "yellow"),
    "boss":     (("(=^･ω･^=)ﾉ", "(=^･ω･^=)ノ"), "mène la meute", "magenta"),
    "oops":     (("(=ＴωＴ=)", "(=;ω;=)"), "oups, une erreur", "red"),
    "full":     (("(=ↀ﹏ↀ=)", "(=ↀ﹏ↀ=)~"), "a trop mangé de contexte", "orange"),
    "tired":    (("(=～ω～=)", "(=～ω～=)ﾟ"), "épuisé (quota)", "orange"),
    "proud":    (("(=^▽^=)✧", "(=^▽^=)✦"), "fier de son travail", "magenta"),
    "happy":    (("(=^･ω･^=)", "(=^･ｪ･^=)"), "ronronne", "green"),
}

TOOL_MOODS = {
    "Bash": "type",
    "Read": "read", "Grep": "read", "Glob": "read", "NotebookRead": "read",
    "Edit": "write", "Write": "write", "MultiEdit": "write", "NotebookEdit": "write",
    "WebFetch": "hunt", "WebSearch": "hunt",
    "Agent": "boss", "Task": "boss",
}

# Le chat grandit avec l'expérience accumulée dans la session.
STAGES = [(0, "chaton"), (30, "chat"), (120, "matou"), (400, "chat légendaire")]


def pick_mood(data, activity, agents, idle_seconds):
    ctx = get(data, "context_window", "used_percentage", default=0)
    five_h = get(data, "rate_limits", "five_hour", "used_percentage", default=0)
    lines = get(data, "cost", "total_lines_added", default=0)

    if ctx >= 85:
        return "full"
    if five_h >= 90:
        return "tired"
    if activity["kind"] == "error":
        return "oops"
    if agents > 0:
        return "boss"
    if idle_seconds > SLEEP_AFTER_SECONDS:
        return "sleep"
    if activity["kind"] == "tool":
        return TOOL_MOODS.get(activity["tool"], "type")
    if activity["kind"] == "prompt":
        return "listen"
    if activity["kind"] == "thinking":
        return "think"
    if lines >= 300:
        return "proud"
    return "happy"


def render_pet(data):
    transcript = data.get("transcript_path") or ""
    activity, pending = analyse_activity(transcript)
    agents = count_running_agents(transcript, pending) if transcript else 0
    try:
        idle = time.time() - os.path.getmtime(transcript)
    except OSError:
        idle = 0

    xp = count_xp(transcript)
    stage = max((s for s in STAGES if xp >= s[0]), key=lambda s: s[0])
    level = STAGES.index(stage) + 1

    frames, caption, color = MOODS[pick_mood(data, activity, agents, idle)]
    frame = frames[int(time.time()) % 2]
    pet = f"{c(frame, color, 'bold')} {c(PET_NAME, 'bold')}{c(f' niv.{level}', 'dim')} {c(caption, color)}"
    return pet, agents


# --------------------------------------------------------------------------
# Segments de la barre
# --------------------------------------------------------------------------

def bar(percent, width=10):
    percent = max(0, min(100, percent))
    filled = round(percent / 100 * width)
    color = "green" if percent < 60 else "yellow" if percent < 85 else "red"
    return c("▓" * filled, color) + c("░" * (width - filled), "dim") + c(f" {percent:.0f}%", color)


def fmt_duration(ms):
    minutes = int(ms // 60000)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes:02d}" if hours else f"{minutes}min"


def fmt_reset(epoch, with_day):
    when = datetime.fromtimestamp(epoch)
    if with_day:
        days = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
        return f"{days[when.weekday()]} {when:%Hh%M}"
    return f"{when:%Hh%M}"


def segment_model(data):
    name = get(data, "model", "display_name", default="?")
    effort = get(data, "effort", "level")
    text = c(name, "orange", "bold")
    if effort:
        text += c(f" ({effort})", "dim")
    if data.get("fast_mode"):
        text += c(" ⚡", "yellow")
    return text


def segment_context(data):
    pct = get(data, "context_window", "used_percentage")
    if pct is None:
        return c("ctx —", "dim")
    return c("ctx ", "dim") + bar(pct)


def segment_cost(data):
    cost = get(data, "cost", "total_cost_usd", default=0)
    return c(f"${cost:.2f}", "yellow")


def segment_duration(data):
    return c("⏱ " + fmt_duration(get(data, "cost", "total_duration_ms", default=0)), "dim")


def segment_agents(count):
    if not count:
        return c("agents 0", "dim")
    return c(f"agents {count} actif" + ("s" if count > 1 else ""), "magenta", "bold")


def segment_lines(data):
    added = get(data, "cost", "total_lines_added", default=0)
    removed = get(data, "cost", "total_lines_removed", default=0)
    return c(f"+{added}", "green") + c("/", "dim") + c(f"−{removed}", "red")


def segment_limits(data):
    parts = []
    for key, label, with_day in (("five_hour", "5h", False), ("seven_day", "7j", True)):
        window = get(data, "rate_limits", key)
        if not window or window.get("used_percentage") is None:
            continue
        text = c(f"{label} ", "dim") + bar(window["used_percentage"], width=5)
        if window.get("resets_at"):
            text += c(" ↻" + fmt_reset(window["resets_at"], with_day), "dim")
        parts.append(text)
    return "  ".join(parts) if parts else c("quota —", "dim")


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}

    sep = c(" │ ", "dim")
    pet, agents = render_pet(data)
    print(sep.join([
        pet,
        segment_model(data),
        segment_context(data),
        segment_cost(data),
        segment_duration(data),
        segment_agents(agents),
        segment_lines(data),
        segment_limits(data),
    ]))


if __name__ == "__main__":
    main()
