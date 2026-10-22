#!/bin/bash
set -euo pipefail
# Read Error List Script
# Input: $1 = analysis_file (optional, defaults to execution-state.json or legacy build-analysis-complete.json)
# Exit code: 0 on success, 1 on failure
# Output: Parsed complete analysis in JSON format

ANALYSIS_FILE="${1:-}"

USE_STATE_FILE=false

# If no file specified, try consolidated execution-state.json first
if [ -z "$ANALYSIS_FILE" ]; then
    if [ -f ".legacyleap/.agent-state/execution-state.json" ] && [ -f ".legacyleap/scripts/shared/manage-execution-state.sh" ]; then
        BUILD_ANALYSIS=$(bash ".legacyleap/scripts/shared/manage-execution-state.sh" "read_build_analysis" 2>/dev/null)
        if [ -n "$BUILD_ANALYSIS" ] && [ "$BUILD_ANALYSIS" != "{}" ]; then
            # Check if build_analysis has content
            if echo "$BUILD_ANALYSIS" | jq -e '.errors // .warnings // empty' > /dev/null 2>&1; then
                ANALYSIS_FILE=".legacyleap/.agent-state/execution-state.json"
                USE_STATE_FILE=true
            fi
        fi
    fi
    
    # Fallback to legacy file if state file doesn't have build analysis
    if [ -z "$ANALYSIS_FILE" ] && [ -f ".legacyleap/build-analysis-complete.json" ]; then
        ANALYSIS_FILE=".legacyleap/build-analysis-complete.json"
        USE_STATE_FILE=false
    fi
fi

if [ -z "$ANALYSIS_FILE" ]; then
    echo "ERROR: Analysis file not found. Expected: .legacyleap/.agent-state/execution-state.json or .legacyleap/build-analysis-complete.json" >&2
    exit 1
fi

if [ ! -f "$ANALYSIS_FILE" ]; then
    echo "ERROR: Analysis file not found: $ANALYSIS_FILE" >&2
    exit 1
fi

# If using execution-state.json, verify it has build_analysis section
if [ "$ANALYSIS_FILE" = ".legacyleap/.agent-state/execution-state.json" ]; then
    if ! jq -e '.build_analysis' "$ANALYSIS_FILE" > /dev/null 2>&1; then
        echo "ERROR: No build_analysis section found in execution-state.json" >&2
        exit 1
    fi
    USE_STATE_FILE=true
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq command not found. Please install jq for JSON parsing." >&2
    exit 1
fi

# Validate JSON format
if ! jq empty "$ANALYSIS_FILE" 2>/dev/null; then
    echo "ERROR: Invalid JSON format in analysis file" >&2
    exit 1
fi

# Extract data based on file type
if [ "$USE_STATE_FILE" = "true" ]; then
    # Reading from execution-state.json - extract build_analysis section
    DATA_SOURCE=".build_analysis"
    ERRORS=$(jq -c '[.build_analysis.errors.by_category.compilation_errors[]? // .build_analysis.errors.compilation_errors[]?, .build_analysis.errors.by_category.reference_errors[]? // .build_analysis.errors.reference_errors[]?, .build_analysis.errors.by_category.syntax_errors[]? // .build_analysis.errors.syntax_errors[]?, .build_analysis.errors.by_category.type_errors[]? // .build_analysis.errors.type_errors[]?, .build_analysis.errors.by_category.nullable_errors[]? // .build_analysis.errors.nullable_errors[]?, .build_analysis.errors.by_category.other_errors[]? // .build_analysis.errors.other_errors[]?]' "$ANALYSIS_FILE")
    
    WARNINGS=$(jq -c '[.build_analysis.warnings.by_category.code_quality_warnings[]? // .build_analysis.warnings.code_quality_warnings[]?, .build_analysis.warnings.by_category.nullable_warnings[]? // .build_analysis.warnings.nullable_warnings[]?, .build_analysis.warnings.by_category.obsolete_warnings[]? // .build_analysis.warnings.obsolete_warnings[]?, .build_analysis.warnings.by_category.xml_documentation_warnings[]? // .build_analysis.warnings.xml_documentation_warnings[]?, .build_analysis.warnings.by_category.security_warnings[]? // .build_analysis.warnings.security_warnings[]?, .build_analysis.warnings.by_category.performance_warnings[]? // .build_analysis.warnings.performance_warnings[]?, .build_analysis.warnings.by_category.other_warnings[]? // .build_analysis.warnings.other_warnings[]?]' "$ANALYSIS_FILE")
    
    CODE_QUALITY=$(jq -c '.build_analysis.code_quality_issues // {}' "$ANALYSIS_FILE")
    DEPENDENCIES=$(jq -c '.build_analysis.dependency_issues // {}' "$ANALYSIS_FILE")
else
    # Reading from legacy build-analysis-complete.json
    DATA_SOURCE="."
    # Check if this is the new format (build-analysis-complete.json) or legacy format
    HAS_ERRORS=$(jq -e '.errors' "$ANALYSIS_FILE" 2>/dev/null)
    HAS_WARNINGS=$(jq -e '.warnings' "$ANALYSIS_FILE" 2>/dev/null)
    
    if [ -n "$HAS_ERRORS" ] && [ -n "$HAS_WARNINGS" ]; then
        # New format: build-analysis-complete.json
        ERRORS=$(jq -c '[.errors.by_category.compilation_errors[]? // .errors.compilation_errors[]?, .errors.by_category.reference_errors[]? // .errors.reference_errors[]?, .errors.by_category.syntax_errors[]? // .errors.syntax_errors[]?, .errors.by_category.type_errors[]? // .errors.type_errors[]?, .errors.by_category.nullable_errors[]? // .errors.nullable_errors[]?, .errors.by_category.other_errors[]? // .errors.other_errors[]?]' "$ANALYSIS_FILE")
        
        WARNINGS=$(jq -c '[.warnings.by_category.code_quality_warnings[]? // .warnings.code_quality_warnings[]?, .warnings.by_category.nullable_warnings[]? // .warnings.nullable_warnings[]?, .warnings.by_category.obsolete_warnings[]? // .warnings.obsolete_warnings[]?, .warnings.by_category.xml_documentation_warnings[]? // .warnings.xml_documentation_warnings[]?, .warnings.by_category.security_warnings[]? // .warnings.security_warnings[]?, .warnings.by_category.performance_warnings[]? // .warnings.performance_warnings[]?, .warnings.by_category.other_warnings[]? // .warnings.other_warnings[]?]' "$ANALYSIS_FILE")
        
        CODE_QUALITY=$(jq -c '.code_quality_issues // {}' "$ANALYSIS_FILE")
        DEPENDENCIES=$(jq -c '.dependency_issues // {}' "$ANALYSIS_FILE")
    else
        # Legacy format: simple error list
        cat "$ANALYSIS_FILE"
        exit 0
    fi
fi

# Combine into complete analysis
jq -n \
    --argjson errors "$ERRORS" \
    --argjson warnings "$WARNINGS" \
    --argjson code_quality "$CODE_QUALITY" \
    --argjson dependencies "$DEPENDENCIES" \
    '{
        errors: $errors,
        warnings: $warnings,
        code_quality_issues: $code_quality,
        dependency_issues: $dependencies,
        error_count: ($errors | length),
        warning_count: ($warnings | length),
        code_quality_count: (if $code_quality.total_issues then $code_quality.total_issues else 0 end),
        dependency_count: (if $dependencies.duplicate_count then $dependencies.duplicate_count else 0 end)
    }'

exit 0

