from functools import cache

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from core.constants import TOXICITY_THRESHOLD


COMMENT_MAX_LENGTH = 512
MODEL_NAME = 'cointegrated/rubert-tiny-toxicity'


@cache
def get_model_and_tokenizer():
    """
    Ленивая загрузка. Загрузится только при первом вызове.
    @cache гарантирует, что загрузка произойдет ровно один раз
    за жизнь процесса.
    """
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()
    return model, tokenizer


def get_toxicity_score(text: str) -> float:
    """Вернуть оценку токсичности от 0 до 1."""
    model, tokenizer = get_model_and_tokenizer()

    inputs = tokenizer(
        text,
        return_tensors='pt',
        truncation=True,
        padding=True,
        max_length=COMMENT_MAX_LENGTH
    )

    with torch.inference_mode():
        outputs = model(**inputs)
        logits = outputs.logits[0]

        probs = torch.softmax(logits, dim=-1)

        toxic_probability = probs[1].item()

    return toxic_probability


def is_toxic(text: str) -> bool:
    """Определить, достигла ли оценка заданного порога."""
    score = get_toxicity_score(text)
    return score >= TOXICITY_THRESHOLD
