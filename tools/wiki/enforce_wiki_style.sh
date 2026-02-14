#!/bin/bash
# Wiki Style Guide Enforcement Script
# Enforces markdown standards for wiki content

set -euo pipefail

WIKI_DIR="wiki"
REPORT_FILE=""
FIX_MODE=false
REPORT_MODE=false
QUIET=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Counters
TOTAL_ISSUES=0
FIXED_ISSUES=0
MANUAL_ISSUES=0

show_help() {
    cat << EOF
Wiki Style Guide Enforcement

Usage: $(basename "$0") [OPTIONS] [WIKI_DIR]

OPTIONS:
    --fix       Auto-fix fixable issues
    --report    Generate compliance report
    --quiet     Suppress output except errors
    --help      Show this help

DEFAULT WIKI DIR: wiki/
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --fix) FIX_MODE=true; shift ;;
        --report) REPORT_MODE=true; shift ;;
        --quiet) QUIET=true; shift ;;
        --help) show_help; exit 0 ;;
        -*) echo "Unknown option: $1"; show_help; exit 1 ;;
        *) WIKI_DIR="$1"; shift ;;
    esac
done

log_info() { [[ "$QUIET" == "false" ]] && echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { [[ "$QUIET" == "false" ]] && echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check for required tools
check_dependencies() {
    local missing=0
    for tool in grep sed awk; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Missing required tool: $tool"
            missing=1
        fi
    done
    if [[ $missing -gt 0 ]]; then exit 1; fi
}

# Load .wikiignore if exists
load_wikiignore() {
    if [[ -f ".wikiignore" ]]; then
        mapfile -t IGNORE_PATTERNS < <(grep -v '^#' .wikiignore | grep -v '^$' || true)
    else
        IGNORE_PATTERNS=()
    fi
}

# Check if file should be ignored
should_ignore() {
    local file="$1"
    for pattern in "${IGNORE_PATTERNS[@]:-}"; do
        if [[ "$file" == "$pattern" ]] || [[ "$file" == *"$pattern"* ]]; then
            return 0
        fi
    done
    return 1
}

# Check trailing whitespace
check_trailing_whitespace() {
    local file="$1"
    local issues
    issues=$(grep -c '[[:space:]]$' "$file" 2>/dev/null) || issues=0
    [[ -z "$issues" ]] && issues=0
    if [[ "$issues" -gt 0 ]]; then
        if [[ "$FIX_MODE" == "true" ]]; then
            sed -i 's/[[:space:]]*$//' "$file"
            FIXED_ISSUES=$((FIXED_ISSUES + 1))
            log_info "Fixed trailing whitespace in $file"
        else
            MANUAL_ISSUES=$((MANUAL_ISSUES + 1))
            log_warn "$file: $issues lines with trailing whitespace"
        fi
        TOTAL_ISSUES=$((TOTAL_ISSUES + issues))
    fi
}

# Check newline at end of file
check_final_newline() {
    local file="$1"
    if [[ -s "$file" ]]; then
        local last_char
        last_char=$(tail -c1 "$file" | od -An -tx1 | tr -d ' ')
        if [[ "$last_char" != "0a" ]]; then
            MANUAL_ISSUES=$((MANUAL_ISSUES + 1))
            TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
            log_warn "$file: missing newline at end of file"
            if [[ "$FIX_MODE" == "true" ]]; then
                echo "" >> "$file"
                FIXED_ISSUES=$((FIXED_ISSUES + 1))
                log_info "Added newline to $file"
            fi
        fi
    fi
}

# Check for broken links (simple version)
check_broken_links() {
    local file="$1"
    # Check for [text](url) patterns
    grep -oE '\[([^]]+)\]\(([^)]+)\)' "$file" | while read -r link; do
        local url
        url=$(echo "$link" | sed 's/.*](\([^)]*\)).*/\1/')
        # Skip external URLs and anchors
        if [[ "$url" != http* ]] && [[ "$url" != \#* ]] && [[ ! -e "$url" ]]; then
            MANUAL_ISSUES=$((MANUAL_ISSUES + 1))
            TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
            log_warn "$file: broken link to $url"
        fi
    done
}

# Check heading hierarchy
check_heading_hierarchy() {
    local file="$1"
    local prev_level=0
    while IFS= read -r line; do
        if [[ "$line" =~ ^(#{1,6})\ (.+) ]]; then
            local level=${#BASH_REMATCH[1]}
            if [[ $level -gt $((prev_level + 1)) ]] && [[ $prev_level -ne 0 ]]; then
                MANUAL_ISSUES=$((MANUAL_ISSUES + 1))
                TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
                log_warn "$file: heading level jump from $prev_level to $level"
            fi
            prev_level=$level
        fi
    done < "$file"
}

# Process single file
process_file() {
    local file="$1"
    [[ -d "$file" ]] && return
    
    should_ignore "$file" && return
    
    check_trailing_whitespace "$file"
    check_final_newline "$file"
    check_broken_links "$file"
    check_heading_hierarchy "$file"
}

# Main execution
main() {
    log_info "Wiki Style Guide Enforcement"
    log_info "Checking directory: $WIKI_DIR"
    
    check_dependencies
    load_wikiignore
    
    if [[ ! -d "$WIKI_DIR" ]]; then
        log_error "Directory not found: $WIKI_DIR"
        exit 1
    fi
    
    # Find all markdown files
    while IFS= read -r -d '' file; do
        process_file "$file"
    done < <(find "$WIKI_DIR" -name "*.md" -print0)
    
    # Summary
    echo ""
    log_info "Summary:"
    echo "  Total issues: $TOTAL_ISSUES"
    echo "  Auto-fixed: $FIXED_ISSUES"
    echo "  Manual fix: $MANUAL_ISSUES"
    
    if [[ $TOTAL_ISSUES -gt 0 ]]; then
        log_error "Style violations found"
        exit 1
    else
        log_info "All checks passed!"
        exit 0
    fi
}

main
