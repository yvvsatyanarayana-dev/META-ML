import spacy
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from ..config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FeatureExtractor:
    def __init__(self):
        # Load NLP models
        try:
            self.nlp = spacy.load(settings.spacy_model)
            logger.info(f"SpaCy model {settings.spacy_model} loaded.")
        except Exception as e:
            logger.error(f"Failed to load SpaCy model: {e}")
            self.nlp = None

        try:
            self.transformer = SentenceTransformer(settings.transformer_model)
            logger.info(f"Transformer model {settings.transformer_model} loaded.")
        except Exception as e:
            logger.error(f"Failed to load Transformer model: {e}")
            self.transformer = None

    def calculate_readability(self, text: str):
        """Calculate a simple readability score (avg word length + sentence count)."""
        if not self.nlp or not text:
            return 0.0
        
        doc = self.nlp(text)
        sentences = list(doc.sents)
        if not sentences:
            return 0.0
            
        words = [token.text for token in doc if not token.is_punct and not token.is_space]
        if not words:
            return 0.0
            
        avg_word_len = sum(len(w) for w in words) / len(words)
        words_per_sentence = len(words) / len(sentences)
        
        # Simple heuristic for readability complexity
        return (avg_word_len * 0.5) + (words_per_sentence * 0.5)

    def get_text_embeddings(self, text: str):
        """Generate sentence embeddings for project abstract."""
        if not self.transformer or not text:
            return np.zeros(384)  # Default size for MiniLM
        
        embedding = self.transformer.encode([text])[0]
        return embedding

    def classify_topics(self, text: str):
        """Heuristic-based research domain classification."""
        if not text: return ["General ML"]
        domains = {
            "Generative AI": ["llm", "gpt", "generative", "transformer", "diffusion", "gan"],
            "Computer Vision": ["image", "object detection", "segmentation", "vision"],
            "Optimizers": ["optimization", "gradient", "sgd", "adam", "convergence"],
            "Graph ML": ["graph", "gnn", "network", "node"],
            "Audio/Speech": ["audio", "speech", "asr", "whisper", "sound"]
        }
        
        tags = []
        text_lower = text.lower()
        for domain, keywords in domains.items():
            if any(k in text_lower for k in keywords):
                tags.append(domain)
        
        return tags if tags else ["Research Baseline"]

    def calculate_sota_similarity(self, embedding):
        """Estimate innovation delta vs industry benchmarks (SOTA Mesh)."""
        # Simulated SOTA benchmarks (representing centroids of high-alpha models)
        sota_benchmarks = [
            np.random.normal(0, 0.05, 384), # Llama-3 Latent Space
            np.random.normal(0.1, 0.05, 384) # Mistral Centroid
        ]
        
        # Calculate max cosine similarity
        similarities = [np.dot(embedding, s) / (np.linalg.norm(embedding) * np.linalg.norm(s)) for s in sota_benchmarks]
        return float(max(similarities))

    def engineer_github_features(self, repo_data: dict):
        """Normalize and derive features from raw GitHub data."""
        if not repo_data:
            return {}
            
        # Example feature engineering
        days_since_creation = (datetime.now() - repo_data["created_at"].replace(tzinfo=None)).days
        commit_velocity = repo_data["commits_count"] / max(days_since_creation, 1)
        
        return {
            "star_count": repo_data["stars"],
            "fork_count": repo_data["forks"],
            "commit_velocity": commit_velocity,
            "readme_score": np.log1p(repo_data["readme_length"]),
            "has_tests": repo_data["has_test_files"],
            "contributor_density": repo_data["contributors_count"] / max(repo_data["commits_count"], 1)
        }

    def prepare_training_row(self, project_data, github_data, author_data):
        """Combine all signals into a single feature vector for modeling."""
        # 1. Text Features
        readability = self.calculate_readability(project_data.get("abstract", ""))
        embeddings = self.get_text_embeddings(project_data.get("abstract", ""))
        
        # 2. GitHub Features
        gh_features = self.engineer_github_features(github_data)
        
        # 3. Author Features
        avg_h_index = 0
        if author_data:
            avg_h_index = sum(a["h_index"] for a in author_data) / len(author_data)
            
        # Combine into a dictionary
        features = {
            "readability": readability,
            "avg_h_index": avg_h_index,
            **gh_features
        }
        
        # In a real scenario, we'd concatenate features + embeddings
        return features, embeddings
