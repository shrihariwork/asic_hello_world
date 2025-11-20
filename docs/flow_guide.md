# OpenLane Flow Execution Guide - Complete Walkthrough

## Prerequisites
```bash
# Ensure OpenLane is installed and environment is set up
export OPENLANE_ROOT=/path/to/openlane
export PDK_ROOT=/path/to/skywater-pdk
```

---

## Flow Execution Commands

### Method 1: Interactive Flow (Recommended for Learning)
```bash
cd $OPENLANE_ROOT
make mount

# Inside the Docker container:
./flow.tcl -interactive

# Then execute step by step:
package require openlane 0.9
prep -design /project/openlane/counter
run_synthesis
run_floorplan
run_placement
run_cts
run_routing
run_magic
run_magic_spice_export
run_magic_drc
run_lvs
run_antenna_check
```

### Method 2: Automated Flow
```bash
cd $OPENLANE_ROOT
make mount
./flow.tcl -design /project/openlane/counter
```

---

## Stage-by-Stage Breakdown

## 1. SYNTHESIS (Yosys)

### What Happens:
- **Tool**: Yosys
- **Input**: RTL Verilog (`counter.v`)
- **Output**: Gate-level netlist using Sky130 standard cells
- **Duration**: ~30 seconds for simple designs

### Process:
1. RTL is parsed and elaborated
2. High-level synthesis converts RTL to generic gates
3. Technology mapping maps generic gates to Sky130 cells
4. Optimization based on `SYNTH_STRATEGY`
5. Generates `.v` netlist and synthesis reports

### Key Artifacts:
```
runs/<run_name>/results/synthesis/
├── counter.v              # Gate-level netlist
└── counter.synthesis.v    # Synthesis netlist

runs/<run_name>/reports/synthesis/
├── 1-synthesis.AREA_0.stat.rpt        # Area report
├── 1-synthesis.AREA_0.chk.rpt         # Check report
└── yosys_4.stat.rpt                   # Statistics
```

### Manual Intervention Points:
- ❌ **Synthesis fails with timing violations**
  - **Fix**: Increase `CLOCK_PERIOD` or change `SYNTH_STRATEGY` to `DELAY 0`
- ❌ **Unmapped cells or missing primitives**
  - **Fix**: Check RTL for unsupported constructs (e.g., latches, tri-state buffers)
- ❌ **Excessive area**
  - **Fix**: Optimize RTL or change `SYNTH_STRATEGY` to `AREA 1` or higher

### Automation Opportunity:
**Parse synthesis reports to extract**:
- Total cell count
- Critical path delay
- Area utilization
- Unmapped cells (errors)

---

## 2. FLOORPLANNING (OpenROAD)

### What Happens:
- **Tool**: OpenROAD (TritonFP)
- **Input**: Gate-level netlist
- **Output**: Die area, core area, IO placement, power grid
- **Duration**: ~10-20 seconds

### Process:
1. Calculate die size based on `FP_CORE_UTIL`
2. Place IO pins
3. Generate power distribution network (PDN)
4. Create placement blockages
5. Define core and die boundaries

### Key Artifacts:
```
runs/<run_name>/results/floorplan/
└── counter.def            # Floorplan DEF

runs/<run_name>/reports/floorplan/
├── 2-initial_fp.rpt       # Floorplan report
└── 3-pdn.rpt              # PDN report
```

### Manual Intervention Points:
- ❌ **Die size too large**
  - **Fix**: Increase `FP_CORE_UTIL` (more dense packing)
- ❌ **PDN generation fails**
  - **Fix**: Check `FP_PDN_VPITCH` and `FP_PDN_HPITCH` values for Sky130
- ❌ **IO pin placement conflicts**
  - **Fix**: Manually specify pin locations in `pin_order.cfg`

### Automation Opportunity:
**Parse floorplan DEF to extract**:
- Die dimensions
- Core area vs. die area ratio
- Power grid coverage
- IO pin count and distribution

---

## 3. PLACEMENT (OpenROAD)

### What Happens:
- **Tool**: OpenROAD (RePlAce + OpenDP)
- **Input**: Floorplan DEF + netlist
- **Output**: Placed standard cells
- **Duration**: ~1-2 minutes

### Process:
1. **Global Placement** (RePlAce): Coarse placement, cells can overlap
2. **Detailed Placement** (OpenDP): Legalize placement, remove overlaps
3. **Optimization**: Buffer insertion, resizing for timing

### Key Artifacts:
```
runs/<run_name>/results/placement/
└── counter.def            # Placed DEF

runs/<run_name>/reports/placement/
├── 5-global_placement.rpt
├── 6-detailed_placement.rpt
└── placement_utilization.rpt
```

### Manual Intervention Points:
- ❌ **Placement fails with overflow**
  - **Fix**: Reduce `PL_TARGET_DENSITY` by 0.05-0.1
- ❌ **High congestion warnings**
  - **Fix**: Reduce `FP_CORE_UTIL` or `PL_TARGET_DENSITY`
- ❌ **Timing violations after placement**
  - **Fix**: Enable `SYNTH_SIZING` and `SYNTH_BUFFERING`

### Automation Opportunity:
**Parse placement reports to extract**:
- Placement density
- Overflow metrics
- Congestion hotspots
- Timing slack (setup/hold)

---

## 4. CLOCK TREE SYNTHESIS (OpenROAD)

### What Happens:
- **Tool**: OpenROAD (TritonCTS)
- **Input**: Placed DEF + clock nets
- **Output**: Clock tree with buffers
- **Duration**: ~30 seconds

### Process:
1. Identify clock nets from `CLOCK_PORT`
2. Build balanced clock tree to minimize skew
3. Insert clock buffers
4. Optimize for skew and latency

### Key Artifacts:
```
runs/<run_name>/results/cts/
└── counter.def            # CTS DEF

runs/<run_name>/reports/cts/
├── 8-cts.rpt              # CTS report
└── cts_skew.rpt           # Skew analysis
```

### Manual Intervention Points:
- ❌ **High clock skew**
  - **Fix**: Adjust `CTS_TARGET_SKEW` or `CTS_CLK_BUFFER_LIST`
- ❌ **Clock tree too large (area overhead)**
  - **Fix**: Relax skew constraints
- ❌ **Setup timing violations after CTS**
  - **Fix**: Increase `CLOCK_PERIOD` or optimize critical paths

### Automation Opportunity:
**Parse CTS reports to extract**:
- Clock skew (min/max)
- Clock latency
- Number of clock buffers inserted
- Clock tree power consumption

---

## 5. ROUTING (OpenROAD + TritonRoute)

### What Happens:
- **Tool**: OpenROAD (FastRoute) + TritonRoute
- **Input**: CTS DEF
- **Output**: Fully routed design
- **Duration**: ~2-5 minutes (most time-consuming)

### Process:
1. **Global Routing** (FastRoute): Assign nets to routing tracks
2. **Detailed Routing** (TritonRoute): Create actual metal geometries
3. **Optimization**: Fix DRC violations, antenna violations

### Key Artifacts:
```
runs/<run_name>/results/routing/
└── counter.def            # Routed DEF

runs/<run_name>/reports/routing/
├── 10-fastroute.rpt       # Global routing
├── 11-tritonRoute.rpt     # Detailed routing
├── drc_violations.rpt     # DRC errors
└── antenna_violations.rpt # Antenna errors
```

### Manual Intervention Points:
- ❌ **Routing fails with DRC violations**
  - **Fix**: Reduce `PL_TARGET_DENSITY`, increase `GLB_RT_ADJUSTMENT`
- ❌ **Antenna violations**
  - **Fix**: Enable `DIODE_INSERTION_STRATEGY` (already set to 3)
- ❌ **Routing congestion**
  - **Fix**: Reduce `FP_CORE_UTIL`, increase die size
- ❌ **Timing violations after routing**
  - **Fix**: Increase `CLOCK_PERIOD`, re-run with timing-driven routing

### Automation Opportunity:
**Parse routing reports to extract**:
- DRC violation count by type
- Antenna violation count
- Wire length statistics
- Routing congestion map
- Timing slack (post-route)

---

## 6. SIGNOFF (Magic + Netgen)

### What Happens:
- **Tools**: Magic (DRC, GDSII), Netgen (LVS)
- **Input**: Routed DEF
- **Output**: GDSII, DRC/LVS reports
- **Duration**: ~1-2 minutes

### Process:
1. **Magic DRC**: Design Rule Check on final layout
2. **Magic GDSII Export**: Convert DEF to GDSII
3. **Magic SPICE Export**: Extract SPICE netlist from layout
4. **Netgen LVS**: Layout vs. Schematic verification
5. **Antenna Check**: Final antenna rule verification

### Key Artifacts:
```
runs/<run_name>/results/signoff/
├── counter.gds            # Final GDSII
└── counter.spice          # Extracted SPICE

runs/<run_name>/reports/signoff/
├── drc.rpt                # DRC report
├── lvs.rpt                # LVS report
└── antenna.rpt            # Antenna report
```

### Manual Intervention Points:
- ❌ **DRC violations in final layout**
  - **Fix**: Manually edit layout in Magic or adjust routing parameters
- ❌ **LVS mismatch**
  - **Fix**: Check for missing connections, shorts, or netlist mismatches
- ❌ **Antenna violations**
  - **Fix**: Add more diodes or adjust routing

### Automation Opportunity:
**Parse signoff reports to extract**:
- DRC violation count (should be 0)
- LVS status (PASS/FAIL)
- Antenna violation count
- Final area and power estimates

---

## Summary of Bottlenecks

| Stage | Common Failures | Automation Target |
|-------|----------------|-------------------|
| **Synthesis** | Timing violations, unmapped cells | Parse `.stat.rpt` for timing/area |
| **Floorplan** | Die size issues, PDN failures | Extract die dimensions from DEF |
| **Placement** | Overflow, congestion | Parse congestion maps, density metrics |
| **CTS** | High skew, timing violations | Extract skew/latency from reports |
| **Routing** | DRC, antenna, congestion | Parse violation counts, suggest density reduction |
| **Signoff** | DRC/LVS failures | Parse final reports, flag non-zero violations |

---

## Next Steps
See `automation_proposal.py` for a Python framework to automate report parsing and parameter tuning.
