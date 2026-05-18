from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from interface.llm_client import LlmClientError


@dataclass(frozen=True)
class OpenAILlmClient:
    api_key: str
    model: str = "gpt-5-nano"

    def generate(self, *, prompt: str, context: str | None = None) -> str:
        messages: list[dict[str, str]] = []
        if context:
            messages.append(
                {
                    "role": "system",
                    "content": f"以下は参照情報です。回答の際に活用してください。\n\n{context}",
                }
            )
        messages.append({"role": "user", "content": prompt})

        try:
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(model=self.model, messages=messages)
            content = response.choices[0].message.content
            return content if content is not None else ""
        except Exception as e:
            raise LlmClientError("テキスト生成に失敗しました") from e
