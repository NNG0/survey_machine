from bertopic import BERTopic
from typing import List, Tuple
import sys
import os
from sklearn.feature_extraction.text import CountVectorizer

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from MCP.types import Article


class SimpleBERTopicClusterer:
    def __init__(self, n_topics: int = 5):
        """Initialize BERTopic model for clustering papers"""
        try:
            #Stopwords
            vectorizer = CountVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2
            )

            self.model = BERTopic(
                nr_topics="auto", 
                min_topic_size=3,  
                verbose=False,
                calculate_probabilities=False,
                vectorizer_model=vectorizer
            )
        except Exception as e:
            print(f"Error loading BERTopic: {e}")
            raise

    def generate_visualizations(self, save_path: str = "/app/visualizations/") -> dict:
        """Generate BERTopic visualizations and save as HTML files"""
    
    def cluster_papers(self, articles: List[Article]) -> List[Tuple[Article, int, str]]:
        """Cluster papers into topics using their abstracts"""
        
        # Handle tuples if they come in
        if isinstance(articles[0], tuple):
            articles = [article for article, _ in articles]
        
        # Filter articles with valid abstracts
        valid_articles = [article for article in articles 
                         if article.abstract and len(article.abstract.strip()) > 50]
        
        if len(valid_articles) < 2:
            return [(article, 0, "General Topic") for article in valid_articles]
        
        try:
            abstracts = [article.abstract for article in valid_articles]
            topics, _ = self.model.fit_transform(abstracts)
            
            # Create simple topic labels
            topic_labels = {}
            for topic_id in set(topics):
                if topic_id == -1:
                    topic_labels[topic_id] = "Outliers"
                else:
                    topic_words = self.model.get_topic(topic_id)
                    if topic_words:
                        top_words = [word for word, _ in topic_words[:3]]
                        topic_labels[topic_id] = ", ".join(top_words)
                    else:
                        topic_labels[topic_id] = f"Topic {topic_id}"
            
            # Combine results
            clustered_papers = []
            for article, topic_id in zip(valid_articles, topics):
                topic_label = topic_labels.get(topic_id, f"Topic {topic_id}")
                clustered_papers.append((article, topic_id, topic_label))
            
            return clustered_papers
            
        except Exception as e:
            print(f"Error during clustering: {e}")
            return [(article, 0, "General Topic") for article in valid_articles]


async def run_bertopic_clustering_agent(
    research_question: str, 
    articles: List[Article], 
    n_topics: int = 3
) -> List[Tuple[Article, int, str]]:
    """Agent wrapper for BERTopic clustering"""
    
    try:
        clusterer = SimpleBERTopicClusterer(n_topics=n_topics)
        return clusterer.cluster_papers(articles)
        
    except Exception as e:
        print(f"Error in BERTopic agent: {e}")
        return [(article, 0, "General Topic") for article in articles]