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
    if ! { sudo apt-get update -q && sudo apt-get install -y -q "${packages[@]}"; }; then
        echo "Setup failed: could not install ${packages[*]}." >&2
        echo "Check the network, then run: bash lab/setup/postcreate.sh" >&2
        exit 1
    fi
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

# A short welcome in each new terminal, pointing to the next command. It only
# prints (see lab/setup/welcome.sh); COURSEDESK_NO_WELCOME=1 turns it off.
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
welcome_marker="# coursedesk-lab welcome"
if ! grep -qF "$welcome_marker" "$HOME/.bashrc" 2>/dev/null; then
    printf '\n%s\n[ -f "%s" ] && . "%s"\n' "$welcome_marker" \
        "$repo_root/lab/setup/welcome.sh" "$repo_root/lab/setup/welcome.sh" >> "$HOME/.bashrc"
fi

# Check that the tools behave as the lab book expects, on a temporary copy:
# attempts, read-only evidence, the checker and the reference results.
log="$(mktemp)"
if bash "$repo_root/tests/run-tests.sh" > "$log" 2>&1; then
    echo "Lab self-test: $(tail -n 1 "$log")."
    rm -f "$log"
else
    echo "Setup failed: the lab self-test found problems." >&2
    grep '^FAIL' "$log" >&2 || tail -n 20 "$log" >&2
    echo "Full output: $log. Tell your instructor before starting the lab." >&2
    exit 1
fi

echo "Setup complete. Open a new terminal and run: bash lab/start.sh"
