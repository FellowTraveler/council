from __future__ import annotations

from typing import Any, Final, Optional

from council.utils import (
    Parameter,
    greater_than_validator,
    must_read_env_str,
    not_empty_validator,
    prefix_validator,
    zero_to_one_validator,
)

from ...llm_base import LLMConfigurationBase
from ...llm_config_object import LLMConfigSpec, LLMProviders

_env_var_prefix: Final[str] = "GEMINI_"


class GeminiLLMConfiguration(LLMConfigurationBase):
    def __init__(self, model: str, api_key: str) -> None:
        """
        Initialize a new instance

        Args:
            api_key (str): the api key
            model (str):
        """
        super().__init__()
        self._model = Parameter.string(name="model", required=True, value=model, validator=prefix_validator("gemini-"))
        self._api_key = Parameter.string(name="api_key", required=True, value=api_key, validator=not_empty_validator)
        self._temperature = Parameter.float(
            name="temperature", required=False, default=0.0, validator=zero_to_one_validator
        )
        self._top_p = Parameter.float(name="top_p", required=False, validator=zero_to_one_validator)
        self._top_k = Parameter.int(name="top_k", required=False, validator=greater_than_validator(0))

    def model_name(self) -> str:
        return self._model.unwrap()

    @property
    def model(self) -> Parameter[str]:
        """
        Gemini model
        """
        return self._model

    @property
    def api_key(self) -> Parameter[str]:
        """
        Gemini API Key
        """
        return self._api_key

    @property
    def temperature(self) -> Parameter[float]:
        """
        Amount of randomness injected into the response.
        Ranges from 0 to 1.
        Use temp closer to 0 for analytical / multiple choice, and closer to 1 for creative and generative tasks.
        """
        return self._temperature

    @property
    def top_p(self) -> Parameter[float]:
        """
        Use nucleus sampling.
        In nucleus sampling, we compute the cumulative distribution over all the options for each subsequent token in
        decreasing probability order and cut it off once it reaches a particular probability specified by top_p.
        """
        return self._top_p

    @property
    def top_k(self) -> Parameter[int]:
        """
        Only sample from the top K options for each subsequent token.
        Used to remove "long tail" low probability responses.
        """
        return self._top_k

    @staticmethod
    def from_env() -> GeminiLLMConfiguration:
        api_key = must_read_env_str(_env_var_prefix + "API_KEY")
        model = must_read_env_str(_env_var_prefix + "LLM_MODEL")
        config = GeminiLLMConfiguration(model=model, api_key=api_key)
        return config

    @classmethod
    def from_spec(cls, spec: LLMConfigSpec) -> GeminiLLMConfiguration:
        spec.check_provider(LLMProviders.Gemini)

        api_key = spec.provider.must_get_value("apiKey")
        model = spec.provider.must_get_value("model")
        config = GeminiLLMConfiguration(model=str(model), api_key=str(api_key))

        if spec.parameters is not None:
            value: Optional[Any] = spec.parameters.get("temperature", None)
            if value is not None:
                config.temperature.set(float(value))
            value = spec.parameters.get("topP", None)
            if value is not None:
                config.top_p.set(float(value))
            value = spec.parameters.get("topK", None)
            if value is not None:
                config.top_k.set(int(value))

        return config
