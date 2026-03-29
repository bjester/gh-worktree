#!/bin/bash
set -e

echo "=== Integration Test Suite ==="

# Helper functions
assert_dir_exists() {
    if [ ! -d "$1" ]; then
        echo "FAIL: Directory '$1' does not exist"
        exit 1
    fi
}

assert_file_exists() {
    if [ ! -f "$1" ]; then
        echo "FAIL: File '$1' does not exist"
        exit 1
    fi
}

verify_branch() {
    local expected_branch="$1"
    local base_branch="$2"
    local current_branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "$expected_branch" ]; then
        echo "FAIL: $expected_branch branch name mismatch (got: $current_branch)"
        exit 1
    fi

    local merge_base
    merge_base=$(git merge-base HEAD "$base_branch")
    local current_head
    current_head=$(git rev-parse HEAD)
    if [ "$merge_base" != "$current_head" ]; then
        echo "FAIL: $expected_branch is not based off $base_branch"
        exit 1
    fi
}

# Setup
START_DIR=$(pwd)
trap "cd '$START_DIR' && rm -rf playground" EXIT

echo "[SETUP] Creating playground directory..."
mkdir -p playground
cd playground

# Test 1: Init from remote
echo "[TEST 1] Initializing from remote repository..."
uv run gh-worktree init https://github.com/bjester/gh-worktree-recipes.git

echo "[VERIFY 1] Checking worktree structure..."
assert_dir_exists "gh-worktree-recipes"
cd gh-worktree-recipes

assert_dir_exists ".gh"
assert_dir_exists ".bare"
assert_file_exists ".git"
echo "PASS: Worktree structure verified"

# Test 2: Create worktree from default branch
echo "[TEST 2] Creating worktree from default branch..."
uv run gh-worktree create integ-test-default

assert_dir_exists "integ-test-default"
cd integ-test-default
assert_file_exists "AGENTS.md"
rm -rf AGENTS.md .aiassistant/ .gemini/
verify_branch "integ-test-default" "main"
cd ..
echo "PASS: integ-test-default created with correct branch based on main"

# Test 3: Create worktree from main branch
echo "[TEST 3] Creating worktree from main branch..."
uv run gh-worktree create integ-test-branch main

assert_dir_exists "integ-test-branch"
cd integ-test-branch
assert_file_exists "AGENTS.md"
rm -rf AGENTS.md .aiassistant/ .gemini/
verify_branch "integ-test-branch" "main"
cd ..
echo "PASS: integ-test-branch created with correct branch based on main"

# Test 4: Create worktree from remote branch
echo "[TEST 4] Creating worktree from origin/main..."
uv run gh-worktree create integ-test-remote-branch origin/main

assert_dir_exists "integ-test-remote-branch"
cd integ-test-remote-branch
assert_file_exists "AGENTS.md"
rm -rf AGENTS.md .aiassistant/ .gemini/
verify_branch "integ-test-remote-branch" "main"
cd ..
echo "PASS: integ-test-remote-branch created with correct branch based on main"

# Test 5: Error handling - non-existent remote
echo "[TEST 5] Testing error handling for non-existent remote..."
if uv run gh-worktree create integ-test-invalid nonexistent/branch 2>/dev/null; then
    echo "FAIL: Should have failed for non-existent remote"
    exit 1
fi
echo "PASS: Correctly rejected non-existent remote"

# Test 6: Checkout command
echo "[TEST 6] Testing checkout command..."
uv run gh-worktree checkout 2

assert_dir_exists "for-integration"
assert_file_exists "for-integration/README.md"
assert_file_exists "for-integration/AGENTS.md"
cd for-integration
rm -rf AGENTS.md .aiassistant/ .gemini/
cd ..

FIRST_LINE=$(head -n 1 for-integration/README.md)
if [[ "$FIRST_LINE" != *"INTEGRATION TEST"* ]]; then
    echo "FAIL: README.md does not start with 'INTEGRATION TEST' (got: $FIRST_LINE)"
    exit 1
fi
echo "PASS: Checkout created for-integration with correct README"

# Test 7: Cleanup - remove all worktrees
echo "[TEST 7] Cleaning up worktrees..."
uv run gh-worktree rm integ-test-default
uv run gh-worktree rm integ-test-branch
uv run gh-worktree rm integ-test-remote-branch
uv run gh-worktree rm for-integration

if [ -d "integ-test-default" ]; then
    echo "FAIL: integ-test-default/ still exists after rm"
    exit 1
fi
if [ -d "integ-test-branch" ]; then
    echo "FAIL: integ-test-branch/ still exists after rm"
    exit 1
fi
if [ -d "integ-test-remote-branch" ]; then
    echo "FAIL: integ-test-remote-branch/ still exists after rm"
    exit 1
fi
if [ -d "for-integration" ]; then
    echo "FAIL: for-integration/ still exists after rm"
    exit 1
fi
echo "PASS: All worktrees removed"

echo "=== All Integration Tests Passed ==="
