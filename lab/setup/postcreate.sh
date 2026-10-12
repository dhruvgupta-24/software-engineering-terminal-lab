#!/usr/bin/env bash
# Runs once when the Codespace is created (see .devcontainer/devcontainer.json).
set -euo pipefail

# The lab needs these tools. The dev container image normally includes them;
# install any that are missing.
missing=()
for cmd in nano less diff sort uniq cut python3; do
    command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done
if [ "${#missing[@]}" -gt 0 ]; then
    echo "Installing missing tools: ${missing[*]}"
    packages=()
    for cmd in "${missing[@]}"; do
        case "$cmd" in
            diff) packages+=(diffutils) ;;
            sort|uniq|cut) packages+=(coreutils) ;;
            *) packages+=("$cmd") ;;
        esac
    done
    sudo apt-get update -q
    sudo apt-get install -y -q "${packages[@]}"
fi

# Shell settings for the lab, added once to ~/.bashrc.
#  - history -a after every command saves history immediately, so commands
#    from one terminal can be found later even after the terminal is closed.
#  - LC_COLLATE=C makes sort use the same character order for every student.
marker="# coursedesk-lab settings"
if ! grep -qF "$marker" "$HOME/.bashrc" 2>/dev/null; then
    cat >> "$HOME/.bashrc" <<'EOF'

# coursedesk-lab settings
export LC_COLLATE=C
export HISTSIZE=5000
export HISTFILESIZE=10000
shopt -s histappend
PROMPT_COMMAND="history -a${PROMPT_COMMAND:+; $PROMPT_COMMAND}"
EOF
fi

echo "Setup complete. Open a new terminal and run: bash lab/start.sh"
