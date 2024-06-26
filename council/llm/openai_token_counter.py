from __future__ import annotations

import logging
from typing import List, Optional, Sequence

import tiktoken
from tiktoken import Encoding

from . import LLMessageTokenCounterBase, LLMMessage, LLMTokenLimitException

logger = logging.getLogger(__name__)


class OpenAITokenCounter(LLMessageTokenCounterBase):
    """
    See https://github.com/openai/openai-python/blob/main/chatml.md for information on
        how messages are converted to tokens.
        https://platform.openai.com/docs/models/overview for tokens
    """

    def __init__(
        self, encoding: Encoding, model: str, limit: int = -1, tokens_per_message: int = 0, tokens_per_name: int = 0
    ) -> None:
        self._encoding = encoding
        self._model = model
        self._limit = limit
        self._tokens_per_message = tokens_per_message
        self._tokens_per_name = tokens_per_name

    def count_message_token(self, message: LLMMessage) -> int:
        num_tokens = self._tokens_per_message
        num_tokens += len(self._encoding.encode(message.content))
        num_tokens += len(self._encoding.encode(message.role.name))
        if message.name is not None:
            num_tokens += len(self._encoding.encode(message.name))
            num_tokens += self._tokens_per_name
        return num_tokens

    def count_messages_token(self, messages: Sequence[LLMMessage]) -> int:
        result = 0
        for message in messages:
            result += self.count_message_token(message)
        result += 3  # every reply is primed with <|start|>assistant<|message|>

        if 0 < self._limit < result:
            raise LLMTokenLimitException(token_count=result, limit=self._limit, model=self._model, llm_name=None)

        return result

    def filter_first_messages(self, messages: Sequence[LLMMessage], margin: int) -> List[LLMMessage]:
        """
        Filters the first messages from a list of LLM messages based on a token limit margin.

        Args:
            messages (Sequence[LLMMessage]): A list of LLMMessage objects representing the messages.
            margin (int): The token limit margin. The method will keep messages until the token count, including
                          assistant tokens, exceeds (limit + 3 - margin).

        Returns:
            List[LLMMessage]: A filtered list of LLMMessage objects representing the first messages.

        """
        count = 0
        limit = self._limit + 3 - margin
        if limit <= 0:
            return []

        result: List[LLMMessage] = []
        for message in reversed(messages):
            token = self.count_message_token(message)
            if count + token < limit:
                count += token
                result.insert(0, message)
            else:
                break
        return result

    def filter_last_messages(self, messages: Sequence[LLMMessage], margin: int) -> List[LLMMessage]:
        """
        Filters the last messages from a list of LLM messages based on a token limit margin.

        Args:
            messages (Sequence[LLMMessage]): A list of LLMMessage objects representing the messages.
            margin (int): The token limit margin. The method will keep messages until the token count, including
                          assistant tokens, exceeds (limit + 3 - margin).

        Returns:
            List[LLMMessage]: A filtered list of LLMMessage objects representing the first messages.

        """
        count = 0
        limit = self._limit + 3 - margin
        if limit <= 0:
            return []

        result: List[LLMMessage] = []
        for message in messages:
            token = self.count_message_token(message)
            if count + token < limit:
                count += token
                result.append(message)
            else:
                break
        return result

    @property
    def token_limit(self) -> int:
        return self._limit

    @staticmethod
    def from_model(model: str) -> Optional[OpenAITokenCounter]:
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            logger.warning(f"model {model} not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")

        if model in {
            "gpt-3.5-turbo-0301",
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-1106",
            "gpt-3.5-turbo-16k-0613",
        }:
            tokens_limit = 16384 if ("-16k-" in model) or ("-1106" in model) else 4096
            tokens_per_message = 3
            tokens_per_name = 1
        elif model in {
            "gpt-4-0314",
            "gpt-4-0613",
            "gpt-4-32k-0314",
            "gpt-4-32k-0613",
        }:
            tokens_limit = 32768 if "-32k-" in model else 8192
            tokens_per_message = 3
            tokens_per_name = 1
        elif model in {
            "gpt-4o-2024-05-13",
            "gpt-4-1106-preview",
            "gpt-4-0125-preview",
            "gpt-4-turbo-2024-04-09",
            "gpt-4-1106-vision-preview",
        }:
            tokens_limit = 128000
            tokens_per_message = 3
            tokens_per_name = 1
        elif model == "gpt-3.5-turbo-0301":
            tokens_limit = 4096
            tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif model == "gpt-3.5-turbo":
            return OpenAITokenCounter._return_alias(model, "gpt-3.5-turbo-0613")
        elif model == "gpt-3.5-turbo-16k":
            return OpenAITokenCounter._return_alias(model, "gpt-3.5-turbo-16k-0613")
        elif model == "gpt-4o":
            return OpenAITokenCounter._return_alias(model, "gpt-4o-2024-05-13")
        elif model == "gpt-4":
            return OpenAITokenCounter._return_alias(model, "gpt-4-0613")
        elif model == "gpt-4-turbo":
            return OpenAITokenCounter._return_alias(model, "gpt-4-turbo-2024-04-09")
        elif model == "gpt-4-32k":
            return OpenAITokenCounter._return_alias(model, "gpt-4-32k-0613")
        elif model == "gpt-4-turbo-preview":
            return OpenAITokenCounter._return_alias(model, "gpt-4-1106-vision-preview")
        elif model == "gpt-4-vision-preview":
            return OpenAITokenCounter._return_alias(model, "gpt-4-0125-preview")
        else:
            return None

        return OpenAITokenCounter(
            encoding,
            model=model,
            limit=tokens_limit,
            tokens_per_message=tokens_per_message,
            tokens_per_name=tokens_per_name,
        )

    @staticmethod
    def _return_alias(alias: str, last: str) -> Optional[OpenAITokenCounter]:
        logger.warning(f"{alias} may change over time. Returning num tokens assuming {last}.")
        return OpenAITokenCounter.from_model(model=last)
