#!/bin/bash
#
# Convenient script to run tests with proper environment
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}FormoTensor Test Runner${NC}"
echo -e "${BLUE}================================${NC}"

# Activate conda environment
if [ -z "$CONDA_DEFAULT_ENV" ] || [ "$CONDA_DEFAULT_ENV" != "formotensor-env" ]; then
    echo -e "${YELLOW}Activating conda environment...${NC}"
    source ~/miniforge3/etc/profile.d/conda.sh
    conda activate formotensor-env
fi

# Check if formotensor_bridge is installed
if ! python -c "import formotensor_bridge" 2>/dev/null; then
    echo -e "${YELLOW}formotensor_bridge not found. Running REBUILD.sh...${NC}"
    ./REBUILD.sh
fi

# Parse arguments
TEST_TYPE="${1:-simple}"

case "$TEST_TYPE" in
    simple|quick)
        echo -e "${GREEN}Running simple test...${NC}"
        python scripts/test_bridge_simple.py
        ;;
    
    full|functionality)
        echo -e "${GREEN}Running full functionality test...${NC}"
        python scripts/test_bridge_functionality.py
        ;;
    
    large|circuits)
        echo -e "${GREEN}Running large circuits test...${NC}"
        python scripts/test_large_circuits.py
        ;;
    
    viz|visualize)
        echo -e "${GREEN}Running visualization (simple)...${NC}"
        python scripts/visualize_tensornet_simple.py
        ;;
    
    viz-full|visualize-full)
        echo -e "${GREEN}Running visualization (with plots)...${NC}"
        python scripts/visualize_tensornet.py
        ;;
    
    state)
        echo -e "${GREEN}Running state API test...${NC}"
        python scripts/test_state_api.py
        ;;
    
    data)
        echo -e "${GREEN}Running data extraction test...${NC}"
        python scripts/test_data_extraction.py
        ;;
    
    all)
        echo -e "${GREEN}Running all tests...${NC}"
        echo ""
        echo -e "${BLUE}[1/5] Simple test${NC}"
        python scripts/test_bridge_simple.py
        echo ""
        echo -e "${BLUE}[2/5] Functionality test${NC}"
        python scripts/test_bridge_functionality.py
        echo ""
        echo -e "${BLUE}[3/5] Large circuits test${NC}"
        python scripts/test_large_circuits.py
        echo ""
        echo -e "${BLUE}[4/5] State API test${NC}"
        python scripts/test_state_api.py
        echo ""
        echo -e "${BLUE}[5/5] Visualization${NC}"
        python scripts/visualize_tensornet_simple.py
        ;;
    
    *)
        echo "Usage: $0 [test_type]"
        echo ""
        echo "Test types:"
        echo "  simple, quick          - Quick validation test"
        echo "  full, functionality    - Full functionality test"
        echo "  large, circuits        - Large circuits test"
        echo "  viz, visualize         - Simple ASCII visualization"
        echo "  viz-full               - Full visualization with plots"
        echo "  state                  - State API exploration"
        echo "  data                   - Data extraction debug"
        echo "  all                    - Run all tests"
        echo ""
        echo "Examples:"
        echo "  $0 simple              # Quick test"
        echo "  $0 large               # Test large circuits"
        echo "  $0 all                 # Run everything"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✓ Test completed!${NC}"



