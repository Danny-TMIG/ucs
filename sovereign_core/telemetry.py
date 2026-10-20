#!/usr/bin/env python3

class FloatTelemetryEngine:
    @staticmethod
    def compute(raw_events: list) -> dict:
        if not raw_events:
            return {"mean_latency": 0.0, "error_rate": 0.0, "confidence_score": 1.0, "sample_count": 0}
            
        latencies = [float(e.get("latency", 0.0)) for e in raw_events]
        errors = [1.0 if e.get("status", 200) != 200 else 0.0 for e in raw_events]
        confidences = [float(e.get("confidence", 1.0)) for e in raw_events]
        
        return {
            "mean_latency": round(sum(latencies) / float(len(latencies)), 6),
            "error_rate": round(sum(errors) / float(len(errors)), 6),
            "confidence_score": round(sum(confidences) / float(len(confidences)), 6),
            "sample_count": len(raw_events)
        }
