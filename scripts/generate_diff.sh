#!/bin/bash

# Script: generate_diff.sh
# Purpose: Generate HTML difference report between before.md and after.md
# Output: docs/reports/phase_3/diff.html
# Usage: bash scripts/generate_diff.sh

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BEFORE_FILE="$PROJECT_ROOT/examples/before.md"
AFTER_FILE="$PROJECT_ROOT/examples/after.md"
OUTPUT_DIR="$PROJECT_ROOT/docs/reports/phase_3"
OUTPUT_FILE="$OUTPUT_DIR/diff.html"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Difference Report Generator ===${NC}"
echo "Project: PersonalManager"
echo "Task: T-RPT-DIFF"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo

# Validate input files
if [[ ! -f "$BEFORE_FILE" ]]; then
    echo -e "${RED}Error: before.md not found at $BEFORE_FILE${NC}"
    exit 1
fi

if [[ ! -f "$AFTER_FILE" ]]; then
    echo -e "${RED}Error: after.md not found at $AFTER_FILE${NC}"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Generate statistics
BEFORE_LINES=$(wc -l < "$BEFORE_FILE" | xargs)
AFTER_LINES=$(wc -l < "$AFTER_FILE" | xargs)
BEFORE_WORDS=$(wc -w < "$BEFORE_FILE" | xargs)
AFTER_WORDS=$(wc -w < "$AFTER_FILE" | xargs)

echo -e "${YELLOW}Analyzing files...${NC}"
echo "Before: $BEFORE_LINES lines, $BEFORE_WORDS words"
echo "After:  $AFTER_LINES lines, $AFTER_WORDS words"

# Calculate changes
LINES_DIFF=$((AFTER_LINES - BEFORE_LINES))
WORDS_DIFF=$((AFTER_WORDS - BEFORE_WORDS))

# Generate diff content using unified diff
DIFF_CONTENT=$(diff -u "$BEFORE_FILE" "$AFTER_FILE" || true)

# Count additions and deletions from diff
ADDED_LINES=$(echo "$DIFF_CONTENT" | grep -c "^+" | xargs || echo "0")
DELETED_LINES=$(echo "$DIFF_CONTENT" | grep -c "^-" | xargs || echo "0")
# Subtract the file headers (2 lines: --- and +++)
if [[ $ADDED_LINES -gt 0 ]]; then
    ADDED_LINES=$((ADDED_LINES - 1))
fi
if [[ $DELETED_LINES -gt 0 ]]; then
    DELETED_LINES=$((DELETED_LINES - 1))
fi

# Modified lines are harder to calculate precisely, using a heuristic
MODIFIED_LINES=$((ADDED_LINES < DELETED_LINES ? ADDED_LINES : DELETED_LINES))
NET_ADDED=$((ADDED_LINES - MODIFIED_LINES))
NET_DELETED=$((DELETED_LINES - MODIFIED_LINES))

STATS_SUMMARY="${NET_ADDED} added, ${MODIFIED_LINES} modified, ${NET_DELETED} deleted"

echo -e "${GREEN}Statistics: $STATS_SUMMARY${NC}"

# Generate HTML report
cat > "$OUTPUT_FILE" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Difference Report - PersonalManager</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .header h1 {
            margin: 0;
            font-size: 2.5rem;
        }

        .header .meta {
            margin-top: 10px;
            opacity: 0.9;
            font-size: 1.1rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
            border-left: 4px solid #667eea;
        }

        .stat-card h3 {
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .stat-card .value {
            font-size: 2rem;
            font-weight: bold;
            color: #333;
        }

        .diff-container {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .diff-header {
            background: #2d3748;
            color: white;
            padding: 15px 20px;
            font-weight: bold;
        }

        .diff-content {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9rem;
            line-height: 1.4;
            overflow-x: auto;
            max-height: 600px;
            overflow-y: auto;
        }

        .diff-line {
            padding: 2px 20px;
            margin: 0;
            white-space: pre-wrap;
            border-left: 3px solid transparent;
        }

        .diff-added {
            background-color: #d4edda;
            border-left-color: #28a745;
            color: #155724;
        }

        .diff-removed {
            background-color: #f8d7da;
            border-left-color: #dc3545;
            color: #721c24;
        }

        .diff-context {
            background-color: #f8f9fa;
            color: #6c757d;
        }

        .diff-header-line {
            background-color: #e9ecef;
            color: #495057;
            font-weight: bold;
        }

        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }

        .summary-section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .summary-section h2 {
            color: #667eea;
            margin-top: 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Difference Report</h1>
        <div class="meta">
            <strong>Task:</strong> T-RPT-DIFF |
            <strong>Project:</strong> PersonalManager |
            <strong>Generated:</strong> TIMESTAMP_PLACEHOLDER
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <h3>Lines Added</h3>
            <div class="value" style="color: #28a745;">+ADDED_PLACEHOLDER</div>
        </div>
        <div class="stat-card">
            <h3>Lines Modified</h3>
            <div class="value" style="color: #ffc107;">~MODIFIED_PLACEHOLDER</div>
        </div>
        <div class="stat-card">
            <h3>Lines Deleted</h3>
            <div class="value" style="color: #dc3545;">-DELETED_PLACEHOLDER</div>
        </div>
        <div class="stat-card">
            <h3>Total Changes</h3>
            <div class="value">TOTAL_CHANGES_PLACEHOLDER</div>
        </div>
    </div>

    <div class="summary-section">
        <h2>📋 Change Summary</h2>
        <p><strong>Statistics:</strong> STATS_SUMMARY_PLACEHOLDER</p>
        <p><strong>Files Compared:</strong></p>
        <ul>
            <li><code>examples/before.md</code> → BEFORE_LINES_PLACEHOLDER lines</li>
            <li><code>examples/after.md</code> → AFTER_LINES_PLACEHOLDER lines</li>
        </ul>
    </div>

    <div class="diff-container">
        <div class="diff-header">
            📋 Unified Diff: examples/before.md → examples/after.md
        </div>
        <div class="diff-content">
DIFF_CONTENT_PLACEHOLDER
        </div>
    </div>

    <div class="footer">
        <p>Generated by PersonalManager DevOps Pipeline • Task: T-RPT-DIFF</p>
        <p><em>Automated difference analysis for Sprint 3 Phase 3</em></p>
    </div>
</body>
</html>
EOF

# Process diff content for HTML display
DIFF_HTML=""
while IFS= read -r line; do
    # Escape HTML characters
    line=$(echo "$line" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g; s/'"'"'/\&#39;/g')

    # Determine line type and apply appropriate styling
    if [[ $line =~ ^@@.*@@ ]]; then
        DIFF_HTML="$DIFF_HTML            <div class=\"diff-line diff-header-line\">$line</div>\n"
    elif [[ $line =~ ^--- ]] || [[ $line =~ ^\+\+\+ ]]; then
        DIFF_HTML="$DIFF_HTML            <div class=\"diff-line diff-header-line\">$line</div>\n"
    elif [[ $line =~ ^\+ ]]; then
        DIFF_HTML="$DIFF_HTML            <div class=\"diff-line diff-added\">$line</div>\n"
    elif [[ $line =~ ^- ]]; then
        DIFF_HTML="$DIFF_HTML            <div class=\"diff-line diff-removed\">$line</div>\n"
    else
        DIFF_HTML="$DIFF_HTML            <div class=\"diff-line diff-context\">$line</div>\n"
    fi
done <<< "$DIFF_CONTENT"

# Replace placeholders in HTML
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TOTAL_CHANGES=$((NET_ADDED + MODIFIED_LINES + NET_DELETED))

sed -i '' "s/TIMESTAMP_PLACEHOLDER/$TIMESTAMP/g" "$OUTPUT_FILE"
sed -i '' "s/ADDED_PLACEHOLDER/$NET_ADDED/g" "$OUTPUT_FILE"
sed -i '' "s/MODIFIED_PLACEHOLDER/$MODIFIED_LINES/g" "$OUTPUT_FILE"
sed -i '' "s/DELETED_PLACEHOLDER/$NET_DELETED/g" "$OUTPUT_FILE"
sed -i '' "s/TOTAL_CHANGES_PLACEHOLDER/$TOTAL_CHANGES/g" "$OUTPUT_FILE"
sed -i '' "s/STATS_SUMMARY_PLACEHOLDER/$STATS_SUMMARY/g" "$OUTPUT_FILE"
sed -i '' "s/BEFORE_LINES_PLACEHOLDER/$BEFORE_LINES/g" "$OUTPUT_FILE"
sed -i '' "s/AFTER_LINES_PLACEHOLDER/$AFTER_LINES/g" "$OUTPUT_FILE"
sed -i '' "s|DIFF_CONTENT_PLACEHOLDER|$DIFF_HTML|g" "$OUTPUT_FILE"

# Calculate file size
FILE_SIZE=$(du -k "$OUTPUT_FILE" | cut -f1)

echo
echo -e "${GREEN}=== Report Generated Successfully ===${NC}"
echo "📄 Output: $OUTPUT_FILE"
echo "📊 File Size: ${FILE_SIZE} KB"
echo "📈 Statistics: $STATS_SUMMARY"
echo
echo -e "${BLUE}Next: Update docs/SPRINT3_DOCS_INDEX.md with the report link${NC}"