# OpenLane Configuration Parameters - Deep Dive

## Critical Parameters Explained

### 1. **FP_CORE_UTIL** (Floorplanning Core Utilization)
**Value**: 50 (50%)

**What it means**: 
- Percentage of the core area that will be occupied by standard cells
- Core area = Total die area - IO ring area

**Impact**:
- **Lower values (30-40%)**: More whitespace → easier routing, better timing closure, but larger die size (higher cost)
- **Higher values (60-80%)**: Denser design → harder routing, potential congestion, smaller die (lower cost)

**Typical ranges**:
- Simple designs: 40-50%
- Complex designs: 50-70%
- High-performance designs: 30-40% (need routing space)

**Bottleneck**: If routing fails with congestion errors, reduce this value.

---

### 2. **PL_TARGET_DENSITY** (Placement Target Density)
**Value**: 0.55 (55%)

**What it means**:
- Fraction of available placement area that cells should occupy
- Must be ≥ FP_CORE_UTIL/100

**Impact**:
- **Lower values (0.4-0.5)**: More whitespace for routing, easier detail routing, better DRC closure
- **Higher values (0.6-0.8)**: Tighter placement, potential routing congestion, harder to meet timing

**Relationship to FP_CORE_UTIL**:
```
PL_TARGET_DENSITY ≥ FP_CORE_UTIL / 100
```
Example: If FP_CORE_UTIL = 50, then PL_TARGET_DENSITY ≥ 0.50

**Bottleneck**: If detail routing fails or you see DRC violations, reduce this value.

---

### 3. **CLOCK_PERIOD** (Clock Constraint)
**Value**: 10.0 ns (100 MHz)

**What it means**:
- Target clock period for timing analysis
- Drives synthesis optimization and STA (Static Timing Analysis)

**Impact**:
- **Shorter period (higher frequency)**: Aggressive optimization, larger cells, more buffers, harder timing closure
- **Longer period (lower frequency)**: Relaxed timing, smaller cells, easier closure

**How it's used**:
1. **Synthesis**: Yosys optimizes to meet this constraint
2. **CTS**: Clock tree built to minimize skew within this period
3. **STA**: Timing reports show slack relative to this constraint

**Bottleneck**: If you have timing violations (negative slack), increase the period or optimize the critical path.

---

## Other Important Parameters

### SYNTH_STRATEGY
- Controls synthesis optimization goal
- `AREA 0`: Balanced area/timing
- `AREA 1-3`: Increasingly aggressive area optimization
- `DELAY 0-4`: Increasingly aggressive timing optimization

### DIODE_INSERTION_STRATEGY
- Prevents antenna violations during manufacturing
- Strategy 3: Insert diodes during placement (recommended)

### Routing Parameters
- `ROUTING_CORES`: Parallel routing threads
- `GLB_RT_ADJUSTMENT`: Routing congestion margin (0.0-0.3)

---

## Parameter Tuning Strategy

### If synthesis fails:
1. Simplify `SYNTH_STRATEGY`
2. Increase `CLOCK_PERIOD`

### If placement fails:
1. Reduce `PL_TARGET_DENSITY`
2. Reduce `FP_CORE_UTIL`

### If routing fails:
1. Reduce `PL_TARGET_DENSITY` by 0.05
2. Reduce `FP_CORE_UTIL` by 5-10%
3. Increase `GLB_RT_ADJUSTMENT`

### If timing fails:
1. Increase `CLOCK_PERIOD`
2. Change `SYNTH_STRATEGY` to `DELAY 0` or higher
3. Enable `SYNTH_SIZING` and `SYNTH_BUFFERING`

---

## Sky130-Specific Notes

The Sky130 PDK has specific requirements:
- Power grid pitch values (`FP_PDN_VPITCH`, `FP_PDN_HPITCH`) are fixed
- Older process node → typically needs lower utilization (40-50%)
- Metal layers: 5 routing layers available
