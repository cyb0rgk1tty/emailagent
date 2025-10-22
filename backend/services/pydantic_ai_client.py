"""
PydanticAI client configuration for OpenRouter
Provides configured models for all agents
"""
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.settings import ModelSettings
from config import get_settings

settings = get_settings()


def get_extraction_model() -> OpenAIChatModel:
    """Get configured model for extraction agent (structured output)

    Returns:
        OpenAIChatModel configured for OpenRouter with extraction settings
    """
    model_settings = ModelSettings(
        temperature=settings.LLM_TEMPERATURE_EXTRACTION,
        max_tokens=settings.LLM_MAX_TOKENS,
        timeout=settings.LLM_TIMEOUT
    )

    # Create OpenRouter provider with API key
    provider = OpenRouterProvider(api_key=settings.OPENROUTER_API_KEY)

    return OpenAIChatModel(
        model_name=settings.OPENROUTER_EXTRACTION_MODEL,
        provider=provider,
        settings=model_settings
    )


def get_response_model() -> OpenAIChatModel:
    """Get configured model for response agent (text generation)

    Returns:
        OpenAIChatModel configured for OpenRouter with response settings
    """
    model_settings = ModelSettings(
        temperature=settings.LLM_TEMPERATURE_RESPONSE,
        max_tokens=settings.LLM_MAX_TOKENS,
        timeout=settings.LLM_TIMEOUT
    )

    # Create OpenRouter provider with API key
    provider = OpenRouterProvider(api_key=settings.OPENROUTER_API_KEY)

    return OpenAIChatModel(
        model_name=settings.OPENROUTER_RESPONSE_MODEL,
        provider=provider,
        settings=model_settings
    )


def get_model(model_type: str = "extraction") -> OpenAIChatModel:
    """Get model by type

    Args:
        model_type: "extraction" or "response"

    Returns:
        Configured OpenAIChatModel

    Raises:
        ValueError: If model_type is invalid
    """
    if model_type == "extraction":
        return get_extraction_model()
    elif model_type == "response":
        return get_response_model()
    else:
        raise ValueError(f"Unknown model type: {model_type}. Use 'extraction' or 'response'.")
