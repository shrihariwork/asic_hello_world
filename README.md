# ASIC Hello World - OpenLane & Sky130

Complete end-to-end ASIC implementation project demonstrating the full RTL-to-GDSII flow using OpenLane and SkyWater 130nm PDK.

## 🎯 Project Overview

**Design**: 8-bit Up/Down Counter with Reset and Enable  
**Target PDK**: SkyWater Sky130  
**Flow**: OpenLane (Yosys + OpenROAD + Magic)  
**Goal**: Identify bottlenecks and demonstrate Python-based automation

---

## 📁 Project Structure

```
asic_hello_world/
├── rtl/
│   └── counter.v              # 8-bit Up/Down Counter RTL
├── tb/
│   └── counter_tb.v           # Testbench for functional verification
├── openlane/
│   └── config.json            # OpenLane configuration
├── scripts/
│   └── automation_proposal.py # Python automation framework
├── docs/
│   ├── config_parameters.md   # Config parameter deep dive
│   └── flow_guide.md          # Complete flow walkthrough
└── README.md
```

---

## 🚀 Quick Start

### 1. Verify RTL Functionality (Pre-Synthesis)

```bash
# Install iverilog if not already installed
sudo apt-get install iverilog gtkwave

# Run simulation
cd asic_hello_world
iverilog -o counter_sim tb/counter_tb.v rtl/counter.v
vvp counter_sim

# View waveforms
gtkwave counter_tb.vcd
```

### 2. Run OpenLane Flow

```bash
# Set up environment
export OPENLANE_ROOT=/path/to/openlane
export PDK_ROOT=/path/to/skywater-pdk

# Start OpenLane Docker
cd $OPENLANE_ROOT
make mount

# Inside Docker container - Interactive mode
./flow.tcl -interactive
package require openlane 0.9
prep -design /project/openlane/counter
run_synthesis
run_floorplan
run_placement
run_cts
run_routing
run_magic
run_magic_drc
run_lvs

# OR - Automated mode
./flow.tcl -design /project/openlane/counter
```

### 3. Analyze Results

```bash
# View synthesis reports
cat runs/<run_name>/reports/synthesis/1-synthesis.AREA_0.stat.rpt

# View timing reports
cat runs/<run_name>/reports/cts/sta.rpt

# View DRC violations
cat runs/<run_name>/reports/signoff/drc.rpt

# View final GDSII
klayout runs/<run_name>/results/signoff/counter.gds
```

---

## 📊 Key Configuration Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `CLOCK_PERIOD` | 10.0 ns | Target clock frequency (100 MHz) |
| `FP_CORE_UTIL` | 50% | Core area utilization |
| `PL_TARGET_DENSITY` | 0.55 | Placement density |
| `SYNTH_STRATEGY` | AREA 0 | Balanced area/timing optimization |
| `DIODE_INSERTION_STRATEGY` | 3 | Antenna violation prevention |

See [docs/config_parameters.md](docs/config_parameters.md) for detailed explanations.

---

## 🔍 Flow Stages & Bottlenecks

| Stage | Tool | Duration | Common Failures | Fix |
|-------|------|----------|----------------|-----|
| **Synthesis** | Yosys | ~30s | Timing violations | ↑ `CLOCK_PERIOD` |
| **Floorplan** | OpenROAD | ~10s | Die size issues | Adjust `FP_CORE_UTIL` |
| **Placement** | RePlAce/OpenDP | ~1-2m | Overflow, congestion | ↓ `PL_TARGET_DENSITY` |
| **CTS** | TritonCTS | ~30s | High skew | Adjust `CTS_TARGET_SKEW` |
| **Routing** | TritonRoute | ~2-5m | DRC violations | ↓ Density, ↑ `GLB_RT_ADJUSTMENT` |
| **Signoff** | Magic/Netgen | ~1-2m | DRC/LVS failures | Manual layout fixes |

See [docs/flow_guide.md](docs/flow_guide.md) for complete stage-by-stage breakdown.

---

## 🤖 Automation Framework

The `scripts/automation_proposal.py` demonstrates:

1. **Report Parsing**: Extract metrics from Yosys, OpenSTA, and DRC reports
2. **Bottleneck Detection**: Identify timing, area, and routing issues
3. **Parameter Tuning**: Automatically adjust `config.json` based on failures
4. **Iterative Optimization**: Re-run flow with updated parameters

### Key Components:

```python
# Parse synthesis reports
area, errors = SynthesisReportParser.parse_stat_report(report_path)

# Analyze timing
timing, errors = TimingReportParser.parse_sta_report(sta_report)

# Detect bottlenecks
suggestions = BottleneckAnalyzer.analyze_routing(result)

# Auto-tune parameters
tuner.adjust_for_routing_congestion()
```

### Usage:

```bash
python3 scripts/automation_proposal.py
```

---

## 📈 Manual Intervention Points

### Synthesis
- ❌ **Unmapped cells** → Check RTL for unsupported constructs
- ❌ **Timing violations** → Increase `CLOCK_PERIOD` or use `SYNTH_STRATEGY = DELAY 0`

### Placement
- ❌ **Overflow** → Reduce `PL_TARGET_DENSITY` by 0.05-0.10
- ❌ **Congestion** → Reduce `FP_CORE_UTIL` by 5-10%

### Routing
- ❌ **DRC violations** → Reduce density, increase `GLB_RT_ADJUSTMENT`
- ❌ **Antenna violations** → Ensure `DIODE_INSERTION_STRATEGY = 3`

### Signoff
- ❌ **LVS mismatch** → Check for shorts or missing connections
- ❌ **DRC failures** → Manually edit layout in Magic

---

## 🛠️ Automation Opportunities

### High-Priority:
1. **Timing Report Parser**: Extract WNS/TNS from STA reports → Auto-adjust `CLOCK_PERIOD`
2. **DRC Violation Tracker**: Parse DRC reports → Suggest density reduction
3. **Congestion Analyzer**: Parse placement logs → Predict routing failures

### Medium-Priority:
4. **Parameter Sweep**: Grid search over `FP_CORE_UTIL` × `PL_TARGET_DENSITY`
5. **Regression Testing**: Track metrics across design iterations
6. **Visualization**: Plot area vs. timing trade-offs

### Libraries to Use:
- `pandas`: Report data analysis
- `matplotlib/seaborn`: Visualization
- `subprocess`: Flow execution
- `re`: Log parsing

---

## 📚 Documentation

- **[config_parameters.md](docs/config_parameters.md)**: Deep dive into OpenLane parameters
- **[flow_guide.md](docs/flow_guide.md)**: Complete flow walkthrough with commands and artifacts

---

## 🎓 Learning Outcomes

After completing this project, you will understand:

1. ✅ Complete RTL-to-GDSII flow using OpenLane
2. ✅ Impact of `FP_CORE_UTIL` and `PL_TARGET_DENSITY` on routing
3. ✅ How to debug synthesis, placement, and routing failures
4. ✅ Where manual intervention is required in the flow
5. ✅ How to automate report parsing and parameter tuning with Python

---

## 📦 Requirements

- **OpenLane**: v2.0+ (with Docker)
- **PDK**: SkyWater Sky130
- **Simulation**: iverilog, gtkwave
- **Python**: 3.8+ (for automation scripts)
- **Viewer**: KLayout (for GDSII viewing)

---

## 🤝 Contributing

This is a learning project. Feel free to:
- Add more complex designs
- Improve the automation framework
- Add visualization scripts
- Document additional bottlenecks

---

## 📄 License

MIT License - Feel free to use for learning and research.

---

## 🔗 References

- [OpenLane Documentation](https://openlane.readthedocs.io/)
- [SkyWater PDK](https://skywater-pdk.readthedocs.io/)
- [Efabless Caravel](https://caravel-harness.readthedocs.io/)

---

**Author**: Senior ASIC Implementation Engineer  
**Date**: 2025-11-20
