import json

from openai import OpenAI

from .config import OPENAI_API_KEY, OPENAI_MODEL
from .utils.logger import get_logger

logger = get_logger(__name__)

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def chat_json(system: str, user: str, temperature: float = 0.0) -> dict | list:
    client = get_client()
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)
