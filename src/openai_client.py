import json

from openai import AsyncOpenAI, OpenAI

from .config import OPENAI_API_KEY, OPENAI_MODEL
from .utils.logger import get_logger

logger = get_logger(__name__)

_client: OpenAI | None = None
_async_client: AsyncOpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def get_async_client() -> AsyncOpenAI:
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _async_client


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


async def achat_json(system: str, user: str, temperature: float = 0.0) -> dict | list:
    client = get_async_client()
    response = await client.chat.completions.create(
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


async def achat_json_vision(
    system: str,
    text: str,
    images_b64: list[str],
    temperature: float = 0.0,
) -> dict | list:
    """
    Send a multimodal message to GPT-4o with text + page images.
    Falls back to text-only if no images are provided.
    """
    if not images_b64:
        return await achat_json(system, text, temperature)

    client = get_async_client()

    # Build content: text block first, then one image block per page
    user_content: list[dict] = [{"type": "text", "text": text}]
    for b64 in images_b64:
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{b64}",
                "detail": "high",
            },
        })

    response = await client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)
