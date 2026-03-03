#!/usr/bin/env bash
# LoCoMo Benchmark Runner for consolidation-memory
#
# Usage:
#   ./scripts/benchmark.sh              # Run all modes (full, episodes-only, full-context)
#   ./scripts/benchmark.sh --dry-run    # Quick validation with 1 conversation
#   ./scripts/benchmark.sh --mode full  # Run specific mode only
#
# Requirements:
#   - OPENAI_API_KEY environment variable set
#   - pip install -e ".[all,benchmark]"

set -euo pipefail
cd "$(dirname "$0")/.."

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DATASET_URL="https://raw.githubusercontent.com/snap-research/locomo/main/data/locomo10.json"
DATASET_PATH="benchmarks/data/locomo10.json"

# ── Preflight checks ──────────────────────────────────────────────────────────

echo -e "${YELLOW}=== LoCoMo Benchmark Runner ===${NC}"
echo ""

# Check OPENAI_API_KEY
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo -e "${RED}ERROR: OPENAI_API_KEY not set.${NC}"
    echo "  export OPENAI_API_KEY=sk-..."
    exit 1
fi
echo -e "${GREEN}✓${NC} OPENAI_API_KEY is set"

# Check Python dependencies
python -c "import openai" 2>/dev/null || {
    echo -e "${RED}ERROR: openai not installed. Run: pip install -e '.[all,benchmark]'${NC}"
    exit 1
}
echo -e "${GREEN}✓${NC} Python dependencies available"

# Download dataset if needed
if [ ! -f "$DATASET_PATH" ]; then
    echo -e "${YELLOW}Downloading locomo10.json...${NC}"
    mkdir -p benchmarks/data
    curl -sL -o "$DATASET_PATH" "$DATASET_URL"
    echo -e "${GREEN}✓${NC} Dataset downloaded ($(wc -c < "$DATASET_PATH") bytes)"
else
    echo -e "${GREEN}✓${NC} Dataset exists ($(wc -c < "$DATASET_PATH") bytes)"
fi

# Quick validation
TURNS=$(python -c "
import json
from pathlib import Path
data = json.loads(Path('$DATASET_PATH').read_text())
total = sum(len(v) for c in data for k, v in c['conversation'].items() if k.startswith('session_') and not k.endswith('date_time'))
print(total)
")
echo -e "${GREEN}✓${NC} Dataset validated: ${TURNS} total turns across 10 conversations"
echo ""

# ── Run benchmark ─────────────────────────────────────────────────────────────

echo -e "${YELLOW}Starting benchmark...${NC}"
echo "  Args: $*"
echo ""

python -m benchmarks.locomo "$@"

echo ""
echo -e "${GREEN}=== Benchmark complete ===${NC}"
echo "Results saved in benchmarks/results/"
ls -la benchmarks/results/*.json 2>/dev/null || echo "(no results files found)"
