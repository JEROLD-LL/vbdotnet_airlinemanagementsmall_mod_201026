#!/bin/bash
set -euo pipefail
# Clean Build Artifacts Script
# Input: $1 = project_root (optional, default: current directory)
# Exit code: 0 on success, 1 on failure

PROJECT_ROOT="${1:-.}"

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "ERROR: Project root directory not found: $PROJECT_ROOT" >&2
    exit 1
fi

# Clean bin/ and obj/ directories
find "$PROJECT_ROOT" -type d \( -name "bin" -o -name "obj" \) -exec rm -rf {} + 2>/dev/null || true

# Count remaining directories
CLEANED_COUNT=$(find "$PROJECT_ROOT" -type d \( -name "bin" -o -name "obj" \) 2>/dev/null | wc -l | tr -d ' ')

if [ "$CLEANED_COUNT" -eq 0 ]; then
    echo "SUCCESS: Build artifacts cleaned (or none found)"
    exit 0
else
    echo "WARNING: Some build artifacts may still exist" >&2
    exit 0  # Not a fatal error
fi

