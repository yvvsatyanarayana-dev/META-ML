import shap
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from io import BytesIO
import base64
import logging

logger = logging.getLogger(__name__)

class OracleExplainer:
    def __init__(self, model=None):
        self.model = model
        self.explainer = None
        if self.model:
            try:
                # XGBoost specific explainer
                self.explainer = shap.TreeExplainer(self.model)
            except Exception as e:
                logger.error(f"Failed to initialize SHAP explainer: {e}")

    def explain_prediction(self, features_dict: dict):
        """Generate both text-based and visual explanations."""
        features_df = pd.DataFrame([features_dict])
        
        # 1. Natural Language Explanation
        explanation_text = self._generate_text_explanation(features_dict)
        
        # 2. Visual Explanation (SHAP Waterfall)
        shap_image = None
        if self.explainer:
            try:
                shap_values = self.explainer(features_df)
                plt.figure(figsize=(10, 6))
                shap.plots.waterfall(shap_values[0], show=False)
                
                # Save plot to base64 string
                buf = BytesIO()
                plt.savefig(buf, format="png", bbox_inches="tight", transparent=True)
                shap_image = base64.b64encode(buf.getvalue()).decode("utf-8")
                plt.close()
            except Exception as e:
                logger.error(f"Error generating SHAP plot: {e}")

        return {
            "text": explanation_text,
            "image": shap_image
        }

    def _generate_text_explanation(self, features: dict):
        """Turn feature values into human-readable pros and cons."""
        pros = []
        cons = []
        
        # Heuristic rules for explanation
        if features.get("star_count", 0) > 500: pros.append("Strong community social proof (high stars)")
        elif features.get("star_count", 0) < 10: cons.append("Low initial social interest")
        
        if features.get("commit_velocity", 0) > 1.0: pros.append("High engineering activity (frequent commits)")
        elif features.get("commit_velocity", 0) < 0.1: cons.append("Inactive or stagnant development cycle")
        
        if features.get("has_tests", 0): pros.append("Production-ready signals detected (test files present)")
        else: cons.append("Lack of quality assurance files (no tests found)")
        
        if features.get("avg_h_index", 0) > 20: pros.append("Strong research pedigree (high author h-index)")
        
        if features.get("readability", 0) > 6: pros.append("Clear and professional project framing")
        elif features.get("readability", 0) < 3: cons.append("Technical abstract may be difficult for general adoption")

        # Compile final text
        result = "### Analysis Insights\n"
        if pros:
            result += "**Strengths:**\n" + "\n".join([f"- {p}" for p in pros]) + "\n\n"
        if cons:
            result += "**Areas for Improvement:**\n" + "\n".join([f"- {c}" for c in cons]) + "\n"
            
        if not pros and not cons:
            result += "The project shows average signals across traditional success metrics."
            
        return result
