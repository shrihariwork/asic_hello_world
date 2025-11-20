#!/usr/bin/env python3
"""
OpenLane Flow Automation Framework

This script demonstrates a Python-based automation architecture for:
1. Executing OpenLane flow stages
2. Parsing reports and logs
3. Detecting bottlenecks and failures
4. Suggesting parameter adjustments
5. Iterative optimization

Author: Senior ASIC Implementation Engineer
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# Data Structures
# ============================================================================

class FlowStage(Enum):
    """OpenLane flow stages"""
    SYNTHESIS = "synthesis"
    FLOORPLAN = "floorplan"
    PLACEMENT = "placement"
    CTS = "cts"
    ROUTING = "routing"
    SIGNOFF = "signoff"


@dataclass
class TimingMetrics:
    """Timing analysis results"""
    wns: float  # Worst Negative Slack
    tns: float  # Total Negative Slack
    whs: float  # Worst Hold Slack
    ths: float  # Total Hold Slack
    critical_path_delay: float
    clock_period: float
    
    def has_violations(self) -> bool:
        return self.wns < 0 or self.whs < 0


@dataclass
class AreaMetrics:
    """Area utilization results"""
    total_cells: int
    total_area: float
    core_area: float
    die_area: float
    utilization: float  # Percentage


@dataclass
class RoutingMetrics:
    """Routing quality metrics"""
    drc_violations: int
    antenna_violations: int
    wire_length: float
    via_count: int
    congestion_score: float


@dataclass
class StageResult:
    """Result from a flow stage"""
    stage: FlowStage
    success: bool
    duration: float
    timing: Optional[TimingMetrics] = None
    area: Optional[AreaMetrics] = None
    routing: Optional[RoutingMetrics] = None
    errors: List[str] = None
    warnings: List[str] = None


# ============================================================================
# Report Parsers
# ============================================================================

class SynthesisReportParser:
    """Parse Yosys synthesis reports"""
    
    @staticmethod
    def parse_stat_report(report_path: Path) -> Tuple[AreaMetrics, List[str]]:
        """
        Parse synthesis statistics report
        
        Example report format:
        === counter ===
           Number of wires:                 15
           Number of wire bits:             23
           Number of public wires:           5
           Number of public wire bits:      13
           Number of cells:                 10
             sky130_fd_sc_hd__dff_1          8
             sky130_fd_sc_hd__xor2_1         2
        
        Chip area for module '\\counter': 50.123000
        """
        errors = []
        total_cells = 0
        total_area = 0.0
        
        if not report_path.exists():
            errors.append(f"Synthesis report not found: {report_path}")
            return AreaMetrics(0, 0.0, 0.0, 0.0, 0.0), errors
        
        with open(report_path, 'r') as f:
            content = f.read()
        
        # Extract cell count
        cell_match = re.search(r'Number of cells:\s+(\d+)', content)
        if cell_match:
            total_cells = int(cell_match.group(1))
        
        # Extract area
        area_match = re.search(r"Chip area for module.*?:\s+([\d.]+)", content)
        if area_match:
            total_area = float(area_match.group(1))
        
        return AreaMetrics(
            total_cells=total_cells,
            total_area=total_area,
            core_area=0.0,  # Not available in synthesis
            die_area=0.0,
            utilization=0.0
        ), errors


class TimingReportParser:
    """Parse STA (Static Timing Analysis) reports"""
    
    @staticmethod
    def parse_sta_report(report_path: Path) -> Tuple[TimingMetrics, List[str]]:
        """
        Parse OpenSTA timing report
        
        Example format:
        Startpoint: count[0] (rising edge-triggered flip-flop clocked by clk)
        Endpoint: count[7] (rising edge-triggered flip-flop clocked by clk)
        Path Group: clk
        Path Type: max
        
        Point                                    Incr       Path
        -------------------------------------------------------
        clock clk (rise edge)                    0.00       0.00
        ...
        data arrival time                                   8.45
        
        clock clk (rise edge)                   10.00      10.00
        ...
        data required time                                  9.50
        -------------------------------------------------------
        slack (MET)                                         1.05
        """
        errors = []
        wns = 0.0
        tns = 0.0
        whs = 0.0
        
        if not report_path.exists():
            errors.append(f"Timing report not found: {report_path}")
            return TimingMetrics(0, 0, 0, 0, 0, 10.0), errors
        
        with open(report_path, 'r') as f:
            content = f.read()
        
        # Extract worst slack
        slack_matches = re.findall(r'slack \((MET|VIOLATED)\)\s+([-\d.]+)', content)
        if slack_matches:
            slacks = [float(s[1]) for s in slack_matches]
            wns = min(slacks)
            tns = sum(s for s in slacks if s < 0)
        
        return TimingMetrics(
            wns=wns,
            tns=tns,
            whs=whs,
            ths=0.0,
            critical_path_delay=10.0 - wns if wns > 0 else 10.0,
            clock_period=10.0
        ), errors


class RoutingReportParser:
    """Parse routing DRC and violation reports"""
    
    @staticmethod
    def parse_drc_report(report_path: Path) -> Tuple[RoutingMetrics, List[str]]:
        """
        Parse DRC violation report
        
        Example format:
        [INFO] Total DRC violations: 5
        [ERROR] Metal spacing violation at (100, 200)
        [ERROR] Via enclosure violation at (150, 250)
        """
        errors = []
        drc_count = 0
        
        if not report_path.exists():
            return RoutingMetrics(0, 0, 0.0, 0, 0.0), []
        
        with open(report_path, 'r') as f:
            content = f.read()
        
        # Count DRC violations
        drc_match = re.search(r'Total DRC violations:\s+(\d+)', content)
        if drc_match:
            drc_count = int(drc_match.group(1))
        else:
            # Count ERROR lines
            drc_count = len(re.findall(r'\[ERROR\]', content))
        
        if drc_count > 0:
            errors.append(f"Found {drc_count} DRC violations")
        
        return RoutingMetrics(
            drc_violations=drc_count,
            antenna_violations=0,
            wire_length=0.0,
            via_count=0,
            congestion_score=0.0
        ), errors


# ============================================================================
# Flow Executor
# ============================================================================

class OpenLaneFlowExecutor:
    """Execute OpenLane flow stages and collect results"""
    
    def __init__(self, design_path: Path, openlane_root: Path):
        self.design_path = design_path
        self.openlane_root = openlane_root
        self.results: List[StageResult] = []
    
    def run_stage(self, stage: FlowStage) -> StageResult:
        """
        Run a single flow stage
        
        In a real implementation, this would:
        1. Execute the OpenLane Tcl command
        2. Monitor the log output
        3. Parse the results
        4. Return structured metrics
        """
        print(f"[INFO] Running {stage.value}...")
        
        # Mock execution (replace with actual subprocess call)
        # Example:
        # cmd = f"./flow.tcl -design {self.design_path} -tag run1 -run {stage.value}"
        # result = subprocess.run(cmd, shell=True, capture_output=True)
        
        # For demonstration, return mock results
        result = StageResult(
            stage=stage,
            success=True,
            duration=10.0,
            errors=[],
            warnings=[]
        )
        
        self.results.append(result)
        return result
    
    def get_latest_run_dir(self) -> Optional[Path]:
        """Find the most recent run directory"""
        runs_dir = self.design_path / "runs"
        if not runs_dir.exists():
            return None
        
        run_dirs = sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        return run_dirs[0] if run_dirs else None


# ============================================================================
# Bottleneck Analyzer
# ============================================================================

class BottleneckAnalyzer:
    """Analyze flow results and suggest parameter adjustments"""
    
    @staticmethod
    def analyze_synthesis(result: StageResult) -> List[str]:
        """Analyze synthesis results and suggest fixes"""
        suggestions = []
        
        if result.timing and result.timing.has_violations():
            suggestions.append(
                f"⚠️  Timing violations detected (WNS={result.timing.wns:.3f}ns). "
                f"Suggestions:\n"
                f"  1. Increase CLOCK_PERIOD from {result.timing.clock_period} to "
                f"{result.timing.clock_period * 1.2:.1f}\n"
                f"  2. Change SYNTH_STRATEGY to 'DELAY 0' for timing optimization"
            )
        
        if result.area and result.area.total_cells > 10000:
            suggestions.append(
                f"⚠️  Large design ({result.area.total_cells} cells). "
                f"Consider reducing FP_CORE_UTIL to 40-45% to ease routing."
            )
        
        return suggestions
    
    @staticmethod
    def analyze_placement(result: StageResult) -> List[str]:
        """Analyze placement results"""
        suggestions = []
        
        if result.errors:
            for error in result.errors:
                if "overflow" in error.lower():
                    suggestions.append(
                        "⚠️  Placement overflow detected. Suggestions:\n"
                        "  1. Reduce PL_TARGET_DENSITY by 0.05-0.10\n"
                        "  2. Reduce FP_CORE_UTIL by 5-10%"
                    )
                elif "congestion" in error.lower():
                    suggestions.append(
                        "⚠️  Routing congestion predicted. Suggestions:\n"
                        "  1. Reduce PL_TARGET_DENSITY to 0.45-0.50\n"
                        "  2. Increase GLB_RT_ADJUSTMENT to 0.15-0.20"
                    )
        
        return suggestions
    
    @staticmethod
    def analyze_routing(result: StageResult) -> List[str]:
        """Analyze routing results"""
        suggestions = []
        
        if result.routing:
            if result.routing.drc_violations > 0:
                suggestions.append(
                    f"❌ {result.routing.drc_violations} DRC violations found. Suggestions:\n"
                    f"  1. Reduce PL_TARGET_DENSITY to 0.40-0.45\n"
                    f"  2. Reduce FP_CORE_UTIL to 35-40%\n"
                    f"  3. Increase GLB_RT_ADJUSTMENT to 0.20"
                )
            
            if result.routing.antenna_violations > 0:
                suggestions.append(
                    f"⚠️  {result.routing.antenna_violations} antenna violations. "
                    f"Ensure DIODE_INSERTION_STRATEGY=3 in config."
                )
        
        return suggestions


# ============================================================================
# Parameter Tuner
# ============================================================================

class ConfigParameterTuner:
    """Automatically adjust config.json parameters based on failures"""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load config.json"""
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def _save_config(self):
        """Save modified config.json"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def adjust_for_timing_violation(self, wns: float):
        """Adjust parameters to fix timing violations"""
        current_period = self.config.get("CLOCK_PERIOD", 10.0)
        new_period = current_period * 1.2  # 20% relaxation
        
        self.config["CLOCK_PERIOD"] = new_period
        self.config["SYNTH_STRATEGY"] = "DELAY 0"
        
        print(f"[TUNER] Adjusted CLOCK_PERIOD: {current_period} → {new_period}")
        self._save_config()
    
    def adjust_for_routing_congestion(self):
        """Adjust parameters to fix routing congestion"""
        current_density = self.config.get("PL_TARGET_DENSITY", 0.55)
        new_density = max(0.40, current_density - 0.10)
        
        current_util = self.config.get("FP_CORE_UTIL", 50)
        new_util = max(35, current_util - 10)
        
        self.config["PL_TARGET_DENSITY"] = new_density
        self.config["FP_CORE_UTIL"] = new_util
        self.config["GLB_RT_ADJUSTMENT"] = 0.20
        
        print(f"[TUNER] Adjusted PL_TARGET_DENSITY: {current_density} → {new_density}")
        print(f"[TUNER] Adjusted FP_CORE_UTIL: {current_util} → {new_util}")
        self._save_config()


# ============================================================================
# Main Automation Loop
# ============================================================================

def main():
    """
    Main automation loop
    
    This demonstrates a complete automation workflow:
    1. Run OpenLane flow
    2. Parse reports
    3. Detect failures
    4. Adjust parameters
    5. Re-run if needed
    """
    
    # Configuration
    design_path = Path("/home/shrihari/projects/HW/asic_hello_world/openlane")
    openlane_root = Path(os.getenv("OPENLANE_ROOT", "/openlane"))
    config_path = design_path / "config.json"
    
    # Initialize components
    executor = OpenLaneFlowExecutor(design_path, openlane_root)
    analyzer = BottleneckAnalyzer()
    tuner = ConfigParameterTuner(config_path)
    
    max_iterations = 3
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n{'='*60}")
        print(f"ITERATION {iteration}")
        print(f"{'='*60}\n")
        
        # Run flow stages
        stages = [
            FlowStage.SYNTHESIS,
            FlowStage.FLOORPLAN,
            FlowStage.PLACEMENT,
            FlowStage.CTS,
            FlowStage.ROUTING,
            FlowStage.SIGNOFF
        ]
        
        failed_stage = None
        
        for stage in stages:
            result = executor.run_stage(stage)
            
            if not result.success:
                failed_stage = stage
                print(f"[ERROR] {stage.value} failed!")
                break
            
            # Analyze results
            if stage == FlowStage.SYNTHESIS:
                suggestions = analyzer.analyze_synthesis(result)
            elif stage == FlowStage.PLACEMENT:
                suggestions = analyzer.analyze_placement(result)
            elif stage == FlowStage.ROUTING:
                suggestions = analyzer.analyze_routing(result)
            else:
                suggestions = []
            
            if suggestions:
                print(f"\n[ANALYSIS] {stage.value} completed with issues:")
                for suggestion in suggestions:
                    print(f"  {suggestion}")
        
        # If flow completed successfully, exit
        if failed_stage is None:
            print("\n✅ Flow completed successfully!")
            break
        
        # Otherwise, attempt to fix
        print(f"\n[TUNER] Attempting to fix {failed_stage.value} failure...")
        
        # Example: adjust parameters based on failure
        if failed_stage == FlowStage.ROUTING:
            tuner.adjust_for_routing_congestion()
        
        print(f"[INFO] Re-running flow with adjusted parameters...")
    
    # Generate summary report
    print(f"\n{'='*60}")
    print("FLOW SUMMARY")
    print(f"{'='*60}")
    print(f"Total iterations: {iteration}")
    print(f"Stages completed: {len(executor.results)}")
    
    for result in executor.results:
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"  {result.stage.value:15} {status:10} ({result.duration:.1f}s)")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║  OpenLane Flow Automation Framework                          ║
║  Automated Report Parsing & Parameter Tuning                 ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Note: This is a demonstration framework
    # In production, you would:
    # 1. Actually execute OpenLane commands via subprocess
    # 2. Parse real report files from runs/<run_name>/reports/
    # 3. Implement more sophisticated parameter tuning algorithms
    # 4. Add support for pandas DataFrames for report analysis
    # 5. Generate visualization plots (matplotlib/seaborn)
    
    print("[INFO] This is a demonstration framework.")
    print("[INFO] To use in production:")
    print("  1. Set OPENLANE_ROOT environment variable")
    print("  2. Ensure OpenLane Docker is running")
    print("  3. Update paths in main() function")
    print("  4. Implement actual subprocess calls in run_stage()")
    print("\n[INFO] Run with: python3 automation_proposal.py\n")
    
    # Uncomment to run the automation loop
    # main()


# ============================================================================
# Additional Utilities
# ============================================================================

def parse_all_reports(run_dir: Path) -> Dict[str, any]:
    """
    Utility to parse all reports from a run directory
    
    Usage:
        run_dir = Path("runs/RUN_2024.01.01_12.00.00")
        metrics = parse_all_reports(run_dir)
        print(f"DRC violations: {metrics['routing'].drc_violations}")
    """
    reports_dir = run_dir / "reports"
    
    results = {}
    
    # Synthesis
    synth_report = reports_dir / "synthesis" / "1-synthesis.AREA_0.stat.rpt"
    if synth_report.exists():
        area, errors = SynthesisReportParser.parse_stat_report(synth_report)
        results['synthesis'] = {'area': area, 'errors': errors}
    
    # Timing (post-synthesis)
    sta_report = reports_dir / "synthesis" / "sta.rpt"
    if sta_report.exists():
        timing, errors = TimingReportParser.parse_sta_report(sta_report)
        results['timing'] = {'metrics': timing, 'errors': errors}
    
    # Routing
    drc_report = reports_dir / "routing" / "drc_violations.rpt"
    if drc_report.exists():
        routing, errors = RoutingReportParser.parse_drc_report(drc_report)
        results['routing'] = {'metrics': routing, 'errors': errors}
    
    return results
