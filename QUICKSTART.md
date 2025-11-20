# Quick Reference - OpenLane Commands

## Interactive Flow (Recommended for Learning)

```bash
# 1. Start OpenLane Docker
cd $OPENLANE_ROOT
make mount

# 2. Inside Docker container
./flow.tcl -interactive

# 3. Execute step-by-step
package require openlane 0.9
prep -design /project/openlane/counter

# Synthesis
run_synthesis

# Floorplan
run_floorplan

# Placement
run_placement

# Clock Tree Synthesis
run_cts

# Routing
run_routing

# Signoff
run_magic
run_magic_drc
run_lvs
run_antenna_check

# 4. Exit
exit
```

## Automated Flow

```bash
cd $OPENLANE_ROOT
make mount
./flow.tcl -design /project/openlane/counter
```

## Viewing Results

```bash
# Synthesis reports
cat runs/<run_name>/reports/synthesis/1-synthesis.AREA_0.stat.rpt

# Timing
cat runs/<run_name>/reports/cts/sta.rpt

# DRC
cat runs/<run_name>/reports/signoff/drc.rpt

# LVS
cat runs/<run_name>/reports/signoff/lvs.rpt

# View GDSII
klayout runs/<run_name>/results/signoff/counter.gds
```

## Common Fixes

| Problem | Fix |
|---------|-----|
| Timing violations | Increase `CLOCK_PERIOD` in config.json |
| Placement overflow | Reduce `PL_TARGET_DENSITY` by 0.05-0.10 |
| DRC violations | Reduce `PL_TARGET_DENSITY` and `FP_CORE_UTIL` |
| Antenna violations | Set `DIODE_INSERTION_STRATEGY: 3` |
