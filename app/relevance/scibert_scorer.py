"""SciBERT based relevance scorer for research questions vs. paper abstracts."""

from __future__ import annotations

import functools
import threading
from typing import Iterable, List

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from MCP.types import Article

_MODEL_NAME = "allenai/scibert_scivocab_uncased"

_tokenizer_lock = threading.Lock()
_model_lock = threading.Lock()
_tokenizer = None
_model = None


def _load_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        with _tokenizer_lock:
            if _tokenizer is None:
                _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
    return _tokenizer


def _load_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                model = AutoModel.from_pretrained(_MODEL_NAME)
                model.eval()
                model.to(torch.device("cpu"))
                _model = model
    return _model


def _normalize(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm


def _get_embedding(text: str) -> np.ndarray:
    tokenizer = _load_tokenizer()
    model = _load_model()

    inputs = tokenizer(
        text,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )

    with torch.no_grad():
        outputs = model(**inputs)
        cls_embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy().squeeze(0)
    return _normalize(cls_embedding)


def score_articles(
    research_question: str,
    articles: Iterable[Article],
) -> list[float]:
    """Return cosine similarity scores for all articles."""
    if not research_question:
        return [0.0 for _ in articles]

    try:
        question_embedding = _get_embedding(research_question)
    except Exception as exc:  # pragma: no cover - defensive fallback
        print(f"Error embedding research question: {exc}")
        return [0.0 for _ in articles]

    scores: list[float] = []
    for article in articles:
        raw = article.article
        abstract = raw.abstract or ""
        if not abstract.strip():
            scores.append(0.0)
            continue
        text = f"{raw.title or ''} [SEP] {abstract}"
        try:
            emb = _get_embedding(text)
            score = float(np.dot(question_embedding, emb))
        except Exception as exc:  # pragma: no cover - defensive fallback
            print(f"Error scoring article '{raw.title}': {exc}")
            score = 0.0
        scores.append(score)
    return scores


async def score_articles_async(
    research_question: str,
    articles: List[Article],
) -> list[float]:
    """Async wrapper so we can run heavy embedding work off the event loop."""
    import asyncio

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        functools.partial(score_articles, research_question, articles),
    )
