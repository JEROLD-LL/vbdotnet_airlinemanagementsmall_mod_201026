#!/bin/bash
set -euo pipefail
# Categorize Warnings Script
# Input: $1 = warnings_json (JSON array of warnings)
# Exit code: 0 on success, 1 on failure
# Output: Categorized warnings in JSON format

WARNINGS_JSON="$1"

if [ -z "$WARNINGS_JSON" ]; then
    echo "ERROR: Warnings JSON not provided" >&2
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq command not found. Please install jq for JSON parsing." >&2
    exit 1
fi

# Categorize warnings based on error code and message patterns
CATEGORIZED=$(echo "$WARNINGS_JSON" | jq -r '
{
    code_quality_warnings: [
        .[] | select(
            (.code | startswith("CS0162")) or  # Unreachable code
            (.code | startswith("CS0168")) or  # Unused variable
            (.code | startswith("CS0219")) or  # Unused variable assignment
            (.code | startswith("CS0414")) or  # Field assigned but never used
            (.code | startswith("CS0649")) or  # Field never assigned
            (.code | startswith("CS8019")) or  # Unused using directive
            (.message | contains("unreachable")) or
            (.message | contains("unused")) or
            (.message | contains("never used"))
        )
    ],
    nullable_warnings: [
        .[] | select(
            (.code | startswith("CS8600")) or  # Converting null literal
            (.code | startswith("CS8601")) or  # Possible null reference
            (.code | startswith("CS8602")) or  # Dereference of possibly null
            (.code | startswith("CS8603")) or  # Possible null reference return
            (.code | startswith("CS8604")) or  # Possible null argument
            (.code | startswith("CS8605")) or  # Unboxing possibly null
            (.code | startswith("CS8606")) or  # Possible null assignment
            (.code | startswith("CS8607")) or  # Possible null in conditional
            (.code | startswith("CS8608")) or  # Nullability mismatch
            (.code | startswith("CS8609")) or  # Nullability mismatch in return
            (.code | startswith("CS8610")) or  # Nullability mismatch in type
            (.code | startswith("CS8611")) or  # Nullability mismatch in parameter
            (.code | startswith("CS8612")) or  # Nullability mismatch in implicit
            (.code | startswith("CS8613")) or  # Nullability mismatch in return
            (.code | startswith("CS8614")) or  # Nullability mismatch in field
            (.code | startswith("CS8615")) or  # Nullability mismatch in property
            (.code | startswith("CS8616")) or  # Nullability mismatch in parameter
            (.code | startswith("CS8617")) or  # Nullability mismatch in return
            (.code | startswith("CS8618")) or  # Non-nullable field uninitialized
            (.code | startswith("CS8619")) or  # Nullability mismatch in value
            (.code | startswith("CS8620")) or  # Nullability mismatch in argument
            (.code | startswith("CS8621")) or  # Nullability mismatch in return
            (.code | startswith("CS8622")) or  # Nullability mismatch in parameter
            (.code | startswith("CS8624")) or  # Nullability mismatch in argument
            (.code | startswith("CS8625")) or  # Cannot convert null literal
            (.code | startswith("CS8629")) or  # Nullable value type may be null
            (.code | startswith("CS8631")) or  # Type does not match target
            (.code | startswith("CS8632")) or  # Annotation for nullable reference
            (.code | startswith("CS8633")) or  # Nullability in constraints
            (.code | startswith("CS8634")) or  # Type cannot be used as type parameter
            (.code | startswith("CS8767")) or  # Nullability mismatch in parameter
            (.code | startswith("CS8768")) or  # Nullability mismatch in return
            (.code | startswith("CS8769")) or  # Nullability mismatch in type
            (.message | contains("nullable")) or
            (.message | contains("null"))
        )
    ],
    obsolete_warnings: [
        .[] | select(
            (.code | startswith("CS0618")) or  # Obsolete member
            (.code | startswith("CS0619")) or  # Obsolete member (error)
            (.code | startswith("CS0672")) or  # Obsolete member override
            (.message | contains("obsolete")) or
            (.message | contains("deprecated"))
        )
    ],
    xml_documentation_warnings: [
        .[] | select(
            (.code | startswith("CS1570")) or  # XML comment
            (.code | startswith("CS1571")) or  # XML comment parameter
            (.code | startswith("CS1572")) or  # XML comment parameter
            (.code | startswith("CS1573")) or  # XML comment parameter
            (.code | startswith("CS1574")) or  # XML comment cref
            (.code | startswith("CS1587")) or  # XML comment not placed
            (.code | startswith("CS1591")) or  # Missing XML comment
            (.message | contains("XML")) or
            (.message | contains("documentation"))
        )
    ],
    security_warnings: [
        .[] | select(
            (.code | startswith("CS3000")) or  # Methods with variable arguments
            (.code | startswith("CS3001")) or  # Argument type
            (.code | startswith("CS3002")) or  # Return type
            (.code | startswith("CS3003")) or  # Variable type
            (.code | startswith("CS3005")) or  # Identifier differing only in case
            (.code | startswith("CS3006")) or  # Overloaded method
            (.code | startswith("CS3007")) or  # Overloaded method
            (.code | startswith("CS3008")) or  # Identifier
            (.code | startswith("CS3009")) or  # Base type
            (.code | startswith("CS4014")) or  # Call not awaited
            (.message | contains("security")) or
            (.message | contains("await"))
        )
    ],
    performance_warnings: [
        .[] | select(
            (.code | startswith("CS4014")) or  # Call not awaited
            (.code | startswith("CS1998")) or  # Async method lacks await
            (.message | contains("performance")) or
            (.message | contains("async")) or
            (.message | contains("await"))
        )
    ],
    other_warnings: [
        .[] | select(
            (.code | (startswith("CS0162") | not) and
                  (startswith("CS0168") | not) and
                  (startswith("CS0219") | not) and
                  (startswith("CS0414") | not) and
                  (startswith("CS0649") | not) and
                  (startswith("CS8019") | not) and
                  (startswith("CS860") | not) and
                  (startswith("CS861") | not) and
                  (startswith("CS862") | not) and
                  (startswith("CS863") | not) and
                  (startswith("CS876") | not) and
                  (startswith("CS0618") | not) and
                  (startswith("CS0619") | not) and
                  (startswith("CS0672") | not) and
                  (startswith("CS157") | not) and
                  (startswith("CS1587") | not) and
                  (startswith("CS1591") | not) and
                  (startswith("CS300") | not) and
                  (startswith("CS4014") | not) and
                  (startswith("CS1998") | not))
        )
    ]
}')

echo "$CATEGORIZED"
exit 0

