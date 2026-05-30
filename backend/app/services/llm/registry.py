from ...core.config import (
    ALLOW_BYOK,
    ALLOWED_PROVIDERS,
    DEFAULT_PROVIDER,
    GEMINI_API_KEY,
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    OPENAI_COMPAT_BASE_URL,
    OPENAI_COMPAT_API_KEY,
    OPENAI_COMPAT_DEFAULT_MODEL,
    OLLAMA_CLOUD_BASE_URL,
    OLLAMA_CLOUD_DEFAULT_MODEL,
    GROQ_BASE_URL,
    GROQ_API_KEY,
    GROQ_DEFAULT_MODEL,
    TOGETHER_BASE_URL,
    TOGETHER_API_KEY,
    TOGETHER_DEFAULT_MODEL,
    MISTRAL_BASE_URL,
    MISTRAL_API_KEY,
    MISTRAL_DEFAULT_MODEL,
    PERPLEXITY_BASE_URL,
    PERPLEXITY_API_KEY,
    PERPLEXITY_DEFAULT_MODEL,
)
from .errors import ProviderAuthError, ProviderNotAllowed
from .anthropic_provider import AnthropicProvider
from .gemini import GeminiProvider
from .ollama_provider import OllamaProvider
from .openai_compatible import OpenAICompatibleProvider
from .openai_provider import OpenAIProvider


def get_provider(
    name: str | None,
    byok_key: str | None,
    allowed_providers: list[str] | None = None,
    allow_byok: bool | None = None,
):
    provider_name = (name or DEFAULT_PROVIDER).strip().lower()
    allowed = allowed_providers or ALLOWED_PROVIDERS
    byok_allowed = ALLOW_BYOK if allow_byok is None else allow_byok
    if provider_name not in allowed:
        raise ProviderNotAllowed("Provider is not enabled.")

    if provider_name == "gemini":
        api_key = GEMINI_API_KEY
        if not api_key:
            if byok_allowed and byok_key:
                api_key = byok_key
            else:
                raise ProviderAuthError("Provider API key not configured.")
        return GeminiProvider(api_key=api_key)

    if provider_name == "openai":
        api_key = OPENAI_API_KEY
        if not api_key:
            if byok_allowed and byok_key:
                api_key = byok_key
            else:
                raise ProviderAuthError("Provider API key not configured.")
        return OpenAIProvider(api_key=api_key)

    if provider_name == "anthropic":
        api_key = ANTHROPIC_API_KEY
        if not api_key:
            if byok_allowed and byok_key:
                api_key = byok_key
            else:
                raise ProviderAuthError("Provider API key not configured.")
        return AnthropicProvider(api_key=api_key)

    if provider_name == "openai_compatible":
        api_key = OPENAI_COMPAT_API_KEY
        if not api_key:
            if byok_allowed and byok_key:
                api_key = byok_key
            else:
                raise ProviderAuthError("Provider API key not configured.")
        if not OPENAI_COMPAT_BASE_URL:
            raise ProviderAuthError("OpenAI-compatible base URL not configured.")
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url=OPENAI_COMPAT_BASE_URL,
            default_model=OPENAI_COMPAT_DEFAULT_MODEL,
        )

    if provider_name == "groq":
        api_key = GROQ_API_KEY
        if not api_key:
            if byok_allowed and byok_key:
                api_key = byok_key
            else:
                raise ProviderAuthError("Provider API key not configured.")
        if not GROQ_BASE_URL:
            raise ProviderAuthError("Groq base URL not configured.")
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url=GROQ_BASE_URL,
            default_model=GROQ_DEFAULT_MODEL,
        )

    if provider_name == "together":
        api_key = TOGETHER_API_KEY
        if not api_key:
            if byok_allowed and byok_key:
                api_key = byok_key
            else:
                raise ProviderAuthError("Provider API key not configured.")
        if not TOGETHER_BASE_URL:
            raise ProviderAuthError("Together base URL not configured.")
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url=TOGETHER_BASE_URL,
            default_model=TOGETHER_DEFAULT_MODEL,
        )

    if provider_name == "mistral":
        api_key = MISTRAL_API_KEY
        if not api_key:
            if byok_allowed and byok_key:
                api_key = byok_key
            else:
                raise ProviderAuthError("Provider API key not configured.")
        if not MISTRAL_BASE_URL:
            raise ProviderAuthError("Mistral base URL not configured.")
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url=MISTRAL_BASE_URL,
            default_model=MISTRAL_DEFAULT_MODEL,
        )

    if provider_name == "perplexity":
        api_key = PERPLEXITY_API_KEY
        if not api_key:
            if byok_allowed and byok_key:
                api_key = byok_key
            else:
                raise ProviderAuthError("Provider API key not configured.")
        if not PERPLEXITY_BASE_URL:
            raise ProviderAuthError("Perplexity base URL not configured.")
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url=PERPLEXITY_BASE_URL,
            default_model=PERPLEXITY_DEFAULT_MODEL,
        )

    if provider_name == "ollama":
        return OllamaProvider(api_key=byok_key if byok_allowed else None)

    if provider_name == "ollama_cloud":
        if not OLLAMA_CLOUD_BASE_URL:
            raise ProviderAuthError("Ollama cloud base URL not configured.")
        return OllamaProvider(
            base_url=OLLAMA_CLOUD_BASE_URL,
            api_key=byok_key if byok_allowed else None,
            default_model=OLLAMA_CLOUD_DEFAULT_MODEL,
        )

    raise ProviderNotAllowed("Provider is not supported.")
