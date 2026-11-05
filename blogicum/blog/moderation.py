import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)
from functools import cache
from core.constants import TOXICITY_THRESHOLD


MODEL_NAME = 'cointegrated/rubert-tiny-toxicity'


@cache
def get_model_and_tokenizer():
    """
    Ленивая загрузка. Загрузится только при первом вызове.
    @cache гарантирует, что загрузка произойдет ровно один раз
    за жизнь процесса.
    """
    print("Загрузка модели ML (это произойдёт только один раз)...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()  # Важно: режим оценки, а не обучения
    return model, tokenizer


def get_toxicity_score(text: str) -> float:
    """Вернуть оценку токсичности от 0 до 1."""
    model, tokenizer = get_model_and_tokenizer()

    inputs = tokenizer(
        text,
        return_tensors='pt',
        truncation=True,
        padding=True,
        max_length=512
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
