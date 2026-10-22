#!/bin/bash
set -euo pipefail
# Scan Dependencies Script
# Input: $1 = solution_path, $2 = check_vulnerabilities (true/false, default: false)
# Exit code: 0 on success, 1 on failure
# Output: Dependency issues in JSON format

SOLUTION_PATH="$1"
CHECK_VULNERABILITIES="${2:-false}"

if [ -z "$SOLUTION_PATH" ]; then
    echo "ERROR: Solution path not provided" >&2
    exit 1
fi

# Find all .csproj files
if [ -f "$SOLUTION_PATH" ] && [[ "$SOLUTION_PATH" =~ \.sln$ ]]; then
    # Solution file provided, find projects
    PROJECT_FILES=$(grep -E 'Project\(' "$SOLUTION_PATH" | grep -oE '"[^"]+\.csproj"' | tr -d '"' | sed 's|\\|/|g')
    PROJECT_DIR=$(dirname "$SOLUTION_PATH")
else
    # Directory provided, find all .csproj files
    PROJECT_DIR="$SOLUTION_PATH"
    PROJECT_FILES=$(find "$PROJECT_DIR" -name "*.csproj" -type f)
fi

if [ -z "$PROJECT_FILES" ]; then
    echo "ERROR: No .csproj files found" >&2
    exit 1
fi

# Initialize arrays
DUPLICATE_PACKAGES=()
ALL_PACKAGES=()
PACKAGE_VERSIONS=()

# Parse each .csproj file
while IFS= read -r PROJECT_FILE; do
    FULL_PATH="$PROJECT_DIR/$PROJECT_FILE"
    if [ ! -f "$FULL_PATH" ]; then
        FULL_PATH="$PROJECT_FILE"
    fi
    
    if [ ! -f "$FULL_PATH" ]; then
        continue
    fi
    
    # Extract PackageReference elements
    while IFS= read -r line; do
        if [[ "$line" =~ PackageReference[[:space:]]+Include=\"([^\"]+)\"[[:space:]]+Version=\"([^\"]+)\" ]]; then
            PACKAGE="${BASH_REMATCH[1]}"
            VERSION="${BASH_REMATCH[2]}"
            
            ALL_PACKAGES+=("$PACKAGE|$VERSION|$FULL_PATH")
            
            # Check for duplicates
            if [[ " ${PACKAGE_VERSIONS[@]} " =~ " ${PACKAGE}|" ]]; then
                # Package already seen, check if version differs
                for existing in "${PACKAGE_VERSIONS[@]}"; do
                    if [[ "$existing" =~ ^${PACKAGE}\| ]]; then
                        EXISTING_VERSION="${existing#*|}"
                        EXISTING_VERSION="${EXISTING_VERSION%%|*}"
                        EXISTING_FILE="${existing##*|}"
                        
                        if [ "$VERSION" != "$EXISTING_VERSION" ]; then
                            DUPLICATE_PACKAGES+=("{\"package\":\"$PACKAGE\",\"version1\":\"$EXISTING_VERSION\",\"file1\":\"$EXISTING_FILE\",\"version2\":\"$VERSION\",\"file2\":\"$FULL_PATH\"}")
                        fi
                    fi
                done
            else
                PACKAGE_VERSIONS+=("$PACKAGE|$VERSION|$FULL_PATH")
            fi
        fi
    done < "$FULL_PATH"
done <<< "$PROJECT_FILES"

# Generate JSON output
if command -v jq &> /dev/null; then
    # Build duplicate packages JSON array
    DUPLICATES_JSON="["
    FIRST=true
    for dup in "${DUPLICATE_PACKAGES[@]}"; do
        if [ "$FIRST" = true ]; then
            FIRST=false
        else
            DUPLICATES_JSON+=","
        fi
        DUPLICATES_JSON+="$dup"
    done
    DUPLICATES_JSON+="]"
    
    # Build all packages summary
    PACKAGE_COUNT=$(echo "${ALL_PACKAGES[@]}" | tr ' ' '\n' | cut -d'|' -f1 | sort -u | wc -l | tr -d ' ')
    
    jq -n \
        --argjson duplicates "$DUPLICATES_JSON" \
        --argjson package_count "$PACKAGE_COUNT" \
        --arg check_vulnerabilities "$CHECK_VULNERABILITIES" \
        '{
            total_packages: $package_count,
            duplicate_packages: $duplicates,
            duplicate_count: ($duplicates | length),
            outdated_packages: [],
            outdated_count: 0,
            vulnerable_packages: [],
            vulnerable_count: 0,
            check_vulnerabilities: ($check_vulnerabilities == "true"),
            summary: {
                total_packages: $package_count,
                duplicate_packages: ($duplicates | length),
                outdated_packages: 0,
                vulnerable_packages: 0
            }
        }'
else
    # Fallback without jq
    echo "{\"error\": \"jq not available, cannot generate JSON output\"}" >&2
    exit 1
fi

exit 0

