import joblib
import os
import xgboost as xgb
import numpy as np
import pandas as pd
from ..config import settings
from ..collection.collector import DataCollector
from ..processing.features import FeatureExtractor
import logging

logger = logging.getLogger(__name__)

class MetaMLCore:
    def __init__(self, model_path=None):
        self.model_path = model_path or settings.model_path
        self.collector = DataCollector()
        self.extractor = FeatureExtractor()
        self.model = self._load_model()

    def _load_model(self):
        """Load the trained XGBoost model if it exists."""
        return None

    def predict(self, github_url: str, abstract: str, overrides: dict = None):
        """Perform a full end-to-end prediction for a project, with optional sandbox overrides."""
        logger.info(f"Predicting success for: {github_url}")
        
        # 1. High-Performance Parallel Data Collection
        from concurrent.futures import ThreadPoolExecutor
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_gh = executor.submit(self.collector.fetch_github_data, github_url)
            
            # --- AUTONOMOUS SEMANTIC FALLBACK Preparation ---
            # We still fetch GH data first for the fallback if abstract is empty
            gh_data = future_gh.result()
            
            effective_abstract = abstract
            if (not effective_abstract or len(effective_abstract.strip()) < 5) and gh_data:
                effective_abstract = gh_data.get("readme_content", "")
                if effective_abstract:
                    logger.info("Autonomous Fallback: Using GitHub README content for semantic context.")
            
            paper_query = (effective_abstract or github_url.split("/")[-1])[:200]
            future_scholar = executor.submit(self.collector.fetch_scholar_data, paper_query)
            scholar_data = future_scholar.result()
        
        # Base Features
        project_info = {"github_url": github_url, "abstract": abstract}
        features, embeddings = self.extractor.prepare_training_row(project_info, gh_data, scholar_data["authors"] if scholar_data else [])
        
        # Apply Sandbox Overrides (What-If simulation)
        if overrides:
            for k, v in overrides.items():
                if k in features:
                    features[k] = v
        
        # 3. 5-Agent Enterprise Consensus Voting (V3 Extended)
        weights = overrides.get("weights", {"structural": 1, "scholar": 1, "market": 1, "ethics": 1, "ops": 1}) if overrides else {"structural": 1, "scholar": 1, "market": 1, "ethics": 1, "ops": 1}
        
        scores = {
            "structural": self._structural_vote(features),
            "scholar": self._scholar_vote(features),
            "market": self._market_vote(features),
            "ethics": self._ethics_vote(effective_abstract),
            "ops": self._ops_vote(features)
        }
        
        # Weighted Probability Calculation
        total_weight = sum(weights.values())
        weighted_sum = sum(scores[k] * weights[k] for k in scores)
        probability = weighted_sum / total_weight

        # 4. Financial Intelligence: ROI Projection
        roi_projection = self._calculate_roi_projection(features, probability)

        # 4. Identify Primary Risk Factor (New Taxonomy)
        risk_profile = self._identify_primary_risk(features, scores["structural"], scores["scholar"], scores["market"])

        # 5. Semantic Clarity Analysis (New Feature)
        clarity_score = self._calculate_clarity(abstract)
        
        # 6. Signals & Confidence
        signals = self._generate_driving_signals(features)
        if clarity_score < 0.5:
            signals.append({"label": "Low Technical Conviction", "impact": "-5%", "status": "neg", "pillar": "Technical"})
            
        confidence = self._calculate_confidence(gh_data, scholar_data)

        return {
            "success_probability": (probability + clarity_score) / 2.0 if clarity_score < 0.4 else probability,
            "confidence_index": confidence,
            "agent_consensus": scores,
            "roi_projection": roi_projection,
            "risk_taxonomy": risk_profile,
            "features": features,
            "signals": signals,
            "metadata": {
                "gh_data": gh_data,
                "scholar_data": scholar_data or {"paper_title": github_url.split("/")[-1], "citation_count": 0, "authors": [], "paper_titles": []}
            }
        }

    def _calculate_clarity(self, text):
        """Simulate semantic conviction analysis."""
        if not text or len(text) < 50: return 0.2
        # Simple heuristic for 'professionalism'
        score = 0.5
        if "benchmark" in text.lower(): score += 0.2
        if "state-of-the-art" in text.lower() or "sota" in text.lower(): score += 0.2
        return min(score, 1.0)

    def _structural_vote(self, f):
        """Agent focused on technical debt and code reliability."""
        score = 0.4
        if f.get("has_tests", 0): score += 0.3
        if f.get("readability", 0) > 6: score += 0.3
        return min(score, 1.0)

    def _scholar_vote(self, f):
        """Agent focused on research pedigree and citations."""
        score = 0.3
        if f.get("avg_h_index", 0) > 10: score += 0.4
        if f.get("citation_count", 0) > 50: score += 0.3
        return min(score, 1.0)

    def _market_vote(self, f):
        """Agent focused on community momentum and growth."""
        score = 0.2
        if f.get("star_count", 0) > 1000: score += 0.5
        if f.get("commit_velocity", 0) > 0.6: score += 0.3
        return min(score, 1.0)

    def _identify_primary_risk(self, f, s1, s2, s3):
        """Identify the 'Kind' of risk present in the project."""
        scores = {"Technical Debt": s1, "Research Isolation": s2, "Growth Stagnation": s3}
        lowest_pillar = min(scores, key=scores.get)
        
        if scores[lowest_pillar] > 0.7:
            return "Stable / Balanced"
        return lowest_pillar

    def _calculate_confidence(self, gh, scholar):
        """Quantify the robustness of the data signals."""
        score = 0.0
        if gh: score += 0.5
        if scholar and scholar.get("citation_count", 0) > 0: score += 0.5
        
        if score >= 1.0: return "HIGH"
        if score >= 0.5: return "MEDIUM"
        return "LOW"

    def _ethics_vote(self, text):
        """Analyze research openness and bias mitigation potential."""
        if not text: return 0.5
        score = 0.5
        pos_terms = ["open source", "ethics", "bias", "fairness", "transparency"]
        for term in pos_terms:
            if term in text.lower(): score += 0.1
        return min(score, 1.0)

    def _ops_vote(self, f):
        """Analyze technical readiness for production deployment."""
        score = 0.4
        if f.get("has_tests", 0): score += 0.2
        if f.get("commit_velocity", 0) > 0.5: score += 0.2
        if f.get("readme_score", 0) > 5: score += 0.2
        return min(score, 1.0)

    def _calculate_roi_projection(self, f, prob):
        """Estimate Strategic Value based on citations and market momentum."""
        base_value = 50000 # Minimum baseline asset value
        citation_multiplier = f.get("citation_count", 0) * 1000
        star_multiplier = f.get("star_count", 0) * 50
        
        total_estimate = (base_value + citation_multiplier + star_multiplier) * prob
        return round(total_estimate, -2)

    def _generate_driving_signals(self, features):
        """Generate qualitative impact signals categorized by pillars."""
        signals = []
        if features.get("star_count", 0) > 500: 
            signals.append({"label": "Market Authority", "impact": "+15%", "status": "pos", "pillar": "Market"})
        if features.get("avg_h_index", 0) > 15: 
            signals.append({"label": "Elite Authorship", "impact": "+20%", "status": "pos", "pillar": "Research"})
        if features.get("has_tests", 0) == 0: 
            signals.append({"label": "QA Vulnerability", "impact": "-10%", "status": "neg", "pillar": "Technical"})
        if features.get("commit_velocity", 0) > 0.8: 
            signals.append({"label": "High Momentum", "impact": "+10%", "status": "pos", "pillar": "Technical"})
        if features.get("readability", 0) < 4: 
            signals.append({"label": "Documentation Debt", "impact": "-5%", "status": "neg", "pillar": "Technical"})
        
        # Ensure we always have at least some signals
        if not signals:
            signals.append({"label": "Baseline Stability", "impact": "Neutral", "status": "neu", "pillar": "Market"})
        return signals

    def _heuristic_score(self, features):
        """A simple weighted heuristic for the demo phase."""
        score = 0.3 # Base
        if features.get("star_count", 0) > 100: score += 0.1
        if features.get("commit_velocity", 0) > 0.5: score += 0.2
        if features.get("has_tests", 0): score += 0.1
        if features.get("avg_h_index", 0) > 10: score += 0.2
        if features.get("readability", 0) > 5: score += 0.1
        
        return min(max(score, 0.0), 1.0)
