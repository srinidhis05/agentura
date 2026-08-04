#!/bin/bash
set -e

# Clone or update a git repo.
# Usage: clone_or_pull <repo_url> <dest> [depth] [branch]
#   branch: if set, checkout that branch; otherwise track remote default
clone_or_pull() {
    local repo_url="$1"
    local dest="$2"
    local depth="${3:-1}"
    local branch="${4:-}"

    [ -z "$repo_url" ] && return

    # Inject token into HTTPS URL for private repos
    if [ -n "$GITHUB_TOKEN" ]; then
        repo_url="${repo_url/https:\/\//https://${GITHUB_TOKEN}@}"
    fi

    if [ -d "$dest/.git" ]; then
        # Clean up any stale lock files from previous crashes
        find "$dest/.git" -name "*.lock" -delete 2>/dev/null || true

        if [ -n "$branch" ]; then
            echo "[entrypoint] Fetching branch '$branch' in $dest"
            git -C "$dest" fetch --depth="$depth" origin "$branch"
            git -C "$dest" checkout -B "$branch" FETCH_HEAD
        else
            echo "[entrypoint] Pulling $dest (default branch)"
            git -C "$dest" fetch --depth="$depth" origin
            git -C "$dest" reset --hard FETCH_HEAD
        fi
    else
        local clone_args=(git clone "--depth=$depth")
        [ -n "$branch" ] && clone_args+=(--branch "$branch")
        echo "[entrypoint] Cloning $repo_url -> $dest (depth=$depth branch=${branch:-default})"
        "${clone_args[@]}" "$repo_url" "$dest"
    fi
}

clone_or_pull "$SKILLS_REPO"         "/skills"                 1   "${SKILLS_BRANCH:-}"
clone_or_pull "$VANCE_ANDROID_REPO"  "/codebase/vance-android" 500
clone_or_pull "$VANCE_IOS_REPO"      "/codebase/vance-ios"     500

# Build code knowledge graphs in the background (non-blocking).
# Graphs are stored in the persistent volume so they survive restarts.
# The executor's query_code_graph tool will serve "[graph] still building"
# until graph.json appears, then switch to live queries automatically.
build_graph_if_stale() {
    local codebase="$1"
    local repo_dir="$2"
    local graph_file="/data/.agentura/graphs/${codebase}/graph.json"

    [ -d "$repo_dir/.git" ] || return

    # Rebuild if graph is missing or older than the most recent git commit
    local repo_mtime
    repo_mtime=$(stat -c %Y "$repo_dir/.git/FETCH_HEAD" 2>/dev/null || echo 0)
    local graph_mtime
    graph_mtime=$(stat -c %Y "$graph_file" 2>/dev/null || echo 0)

    if [ "$graph_mtime" -lt "$repo_mtime" ]; then
        echo "[entrypoint] Building ${codebase} code graph (background)..."
        mkdir -p "/data/.agentura/graphs/${codebase}"
        python3 -m agentura_sdk.runner.graph_builder "$codebase" \
            >> "/data/.agentura/graphs/${codebase}/build.log" 2>&1 &
    else
        echo "[entrypoint] ${codebase} code graph is up to date."
    fi
}

build_graph_if_stale "android" "/codebase/vance-android"
build_graph_if_stale "ios"     "/codebase/vance-ios"

exec agentura-server
