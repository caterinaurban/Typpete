from engine.liveness.liveness_analysis import LivenessAnalysis
from engine.traces.traces_analysis import BoolTracesAnalysis, TvlTracesAnalysis
from engine.usage.usage_analysis import UsageAnalysis

# LivenessAnalysis().main("liveness/example.py")

BoolTracesAnalysis().main("traces/example.py")

# TvlTracesAnalysis().main("traces/example.py")

# UsageAnalysis().main("usage/example.py")
