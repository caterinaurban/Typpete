from engine.liveness.liveness_analysis import LivenessAnalysis
from engine.traces.traces_analysis import TracesAnalysis
from engine.usage.usage_analysis import UsageAnalysis

LivenessAnalysis().main("liveness/example.py")

TracesAnalysis().main("traces/example.py")

UsageAnalysis().main("usage/example.py")
