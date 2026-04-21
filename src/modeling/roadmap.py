import datetime

class IdentityRoadmapGenerator:
    """Generates a prioritized engineering roadmap based on AI audit risks."""
    
    def generate_roadmap(self, signals):
        """Map negative signals to specific technical tasks."""
        roadmap = []
        neg_signals = [s for s in signals if s.get("status") == "neg"]
        
        # Priority mapping
        priority_map = {
            "Technical": "Critical",
            "Research": "Strategic",
            "Market": "Growth"
        }
        
        for i, sig in enumerate(neg_signals):
            task = {
                "id": f"META-{i+1:03d}",
                "phase": f"Month {i+1}",
                "priority": priority_map.get(sig["pillar"], "Medium"),
                "signal": sig["label"],
                "action_item": self._derive_action_item(sig["label"]),
                "impact": sig["impact"]
            }
            roadmap.append(task)
            
        # If no risks, generate maintenance roadmap
        if not roadmap:
            roadmap.append({
                "id": "META-MNT",
                "phase": "Month 1",
                "priority": "Maintenance",
                "signal": "Stability",
                "action_item": "Continuous regression monitoring and dependency hardening.",
                "impact": "Neutral"
            })
            
        return roadmap

    def _derive_action_item(self, label):
        """Map specific signal labels to actionable engineering descriptions."""
        actions = {
            "QA Vulnerability": "Establish CI/CD pipeline with >80% code coverage requirement.",
            "Documentation Debt": "Implement automated docstrings and technical architecture diagrams.",
            "Research Isolation": "Initiate peer-review collaboration and citation network expansion.",
            "Low Technical Conviction": "Refactor technical documentation to include standardized benchmarking results (SOTA).",
            "Growth Stagnation": "Implement community outreach program and feature release frequency increase.",
            "Technical Debt": "Refactor core architectural bottlenecks and reduce cyclomatic complexity."
        }
        return actions.get(label, "General architectural hardening and vulnerability assessment.")
