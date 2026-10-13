# Welcome message for a new terminal in the lab Codespace.
#
# Sourced from ~/.bashrc (added once by lab/setup/postcreate.sh). It only
# prints; it never creates an attempt or changes any file. It stays silent
# unless the shell is interactive and starts at the repository root.
# To turn it off: export COURSEDESK_NO_WELCOME=1 (for example in ~/.bashrc),
# or delete the "# coursedesk-lab welcome" lines from ~/.bashrc.

_coursedesk_welcome() {
    local repo latest
    repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    [[ $- == *i* ]] || return 0
    [ -n "${COURSEDESK_NO_WELCOME:-}" ] && return 0
    [ "$PWD" = "$repo" ] || return 0

    latest="$(ls -d "$repo"/attempts/attempt-* 2>/dev/null | sort -V | tail -n 1)"
    echo "CourseDesk lab (Lab 2). Follow book/lab-book.pdf."
    if [ -z "$latest" ]; then
        echo "  Start here:        bash lab/start.sh"
    else
        echo "  Continue with:     cd $latest"
        echo "  Or start again:    bash lab/start.sh"
    fi
}
_coursedesk_welcome
unset -f _coursedesk_welcome
