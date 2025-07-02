import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
from typing import List, Tuple
import sys
sys.path.append('/app/app')
from MCP.types import Article
    
class SciBERTRelevanceScorer:
    def __init__(self, model_name: str = "allenai/scibert_scivocab_uncased"):
        """Initialize SciBERT model for scientific paper embeddings"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.model.eval()
            
            # Use CPU only for simplicity (change to Mac M1 if needed)
            self.device = torch.device('cpu')
            self.model.to(self.device)
            
        except Exception as e:
            print(f"Error loading SciBERT: {e}")
            raise
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get SciBERT embedding for a text"""
        try:
            inputs = self.tokenizer(
                text, 
                padding=True, 
                truncation=True, 
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                embedding = embedding / np.linalg.norm(embedding)
                return embedding.flatten()
                
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return np.zeros(768)
    
    def score_articles(self, research_question: str, articles: List[Article]) -> List[Tuple[Article, float]]:
        """Score articles by relevance to research question using SciBERT"""
        
        # Filter articles with abstracts
        articles_with_abstracts = [
            article for article in articles 
            if article.abstract and article.abstract.strip() and article.abstract != "No abstract available"
        ]
        
        if not articles_with_abstracts:
            return []
        
        # Get embedding for research question
        question_embedding = self._get_embedding(research_question)
        
        scored_articles = []
        for article in articles_with_abstracts:
            try:
                # Create paper text with title and abstract
                paper_text = f"{article.title} [SEP] {article.abstract}"
                article_embedding = self._get_embedding(paper_text)
                
                # Calculate cosine similarity
                similarity = np.dot(question_embedding, article_embedding)
                scored_articles.append((article, float(similarity)))
                    
            except Exception as e:
                print(f"Error scoring article: {e}")
                scored_articles.append((article, 0.0))
        
        # Sort by relevance score (highest first)
        scored_articles.sort(key=lambda x: x[1], reverse=True)
        return scored_articles
    
    def get_top_papers(self, research_question: str, articles: List[Article], top_k: int = 10) -> List[Tuple[Article, float]]:
        """Get top-k most relevant papers"""
        scored_articles = self.score_articles(research_question, articles)
        return scored_articles[:top_k]


async def run_embedding_relevance_agent(research_question: str, articles: List[Article], top_k: int = 10) -> List[Tuple[Article, float]]:
    """MCP Agent wrapper for SciBERT relevance scoring"""
    
    try:
        scorer = SciBERTRelevanceScorer()
        return scorer.get_top_papers(research_question, articles, top_k)
        
    except Exception as e:
        print(f"Error in SciBERT agent: {e}")
        return [(article, 0.0) for article in articles[:top_k]]