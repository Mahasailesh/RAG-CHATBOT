import os
from pathlib import Path


def _parse_csv(value: str, lower: bool = False) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if lower:
        return [item.lower() for item in items]
    return items


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


API_TITLE = os.getenv("CLEARPASS_API_TITLE", "ClearPass AI API")
API_VERSION = os.getenv("CLEARPASS_API_VERSION", "0.1.0")
ALLOWED_ORIGINS = _parse_csv(os.getenv("CLEARPASS_ALLOWED_ORIGINS", ""))
RATE_LIMIT = os.getenv("CLEARPASS_RATE_LIMIT", "15/minute")
MAX_TEXT_CHARS = int(os.getenv("CLEARPASS_MAX_TEXT_CHARS", "120000"))

ALLOWED_PROVIDERS = _parse_csv(
    os.getenv(
        "CLEARPASS_ALLOWED_PROVIDERS",
        "gemini,openai,anthropic,ollama,ollama_cloud,openai_compatible,groq,together,mistral,perplexity",
    ),
    lower=True,
)
if not ALLOWED_PROVIDERS:
    ALLOWED_PROVIDERS = ["gemini"]

DEFAULT_PROVIDER = os.getenv("CLEARPASS_DEFAULT_PROVIDER", "").strip().lower()
if not DEFAULT_PROVIDER or DEFAULT_PROVIDER not in ALLOWED_PROVIDERS:
    DEFAULT_PROVIDER = ALLOWED_PROVIDERS[0]

ALLOW_BYOK = _parse_bool(os.getenv("CLEARPASS_ALLOW_BYOK", "false"))

GEMINI_API_KEY = os.getenv("CLEARPASS_GEMINI_API_KEY", "").strip() or None
GEMINI_DEFAULT_MODEL = os.getenv("CLEARPASS_GEMINI_MODEL", "gemini-2.5-flash")

OPENAI_API_KEY = os.getenv("CLEARPASS_OPENAI_API_KEY", "").strip() or None
OPENAI_DEFAULT_MODEL = os.getenv("CLEARPASS_OPENAI_MODEL", "gpt-4o-mini")
OPENAI_ORG_ID = os.getenv("CLEARPASS_OPENAI_ORG", "").strip() or None
OPENAI_PROJECT_ID = os.getenv("CLEARPASS_OPENAI_PROJECT", "").strip() or None

ANTHROPIC_API_KEY = os.getenv("CLEARPASS_ANTHROPIC_API_KEY", "").strip() or None
ANTHROPIC_DEFAULT_MODEL = os.getenv(
    "CLEARPASS_ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620"
)

OPENAI_COMPAT_BASE_URL = os.getenv("CLEARPASS_OPENAI_COMPAT_BASE_URL", "").strip()
OPENAI_COMPAT_API_KEY = os.getenv("CLEARPASS_OPENAI_COMPAT_API_KEY", "").strip() or None
OPENAI_COMPAT_DEFAULT_MODEL = os.getenv(
    "CLEARPASS_OPENAI_COMPAT_MODEL", "gpt-4o-mini"
)

GROQ_BASE_URL = os.getenv("CLEARPASS_GROQ_BASE_URL", "").strip()
GROQ_API_KEY = os.getenv("CLEARPASS_GROQ_API_KEY", "").strip() or None
GROQ_DEFAULT_MODEL = os.getenv("CLEARPASS_GROQ_MODEL", "llama-3.1-8b-instant")

TOGETHER_BASE_URL = os.getenv("CLEARPASS_TOGETHER_BASE_URL", "").strip()
TOGETHER_API_KEY = os.getenv("CLEARPASS_TOGETHER_API_KEY", "").strip() or None
TOGETHER_DEFAULT_MODEL = os.getenv(
    "CLEARPASS_TOGETHER_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
)

MISTRAL_BASE_URL = os.getenv("CLEARPASS_MISTRAL_BASE_URL", "").strip()
MISTRAL_API_KEY = os.getenv("CLEARPASS_MISTRAL_API_KEY", "").strip() or None
MISTRAL_DEFAULT_MODEL = os.getenv("CLEARPASS_MISTRAL_MODEL", "mistral-small-latest")

PERPLEXITY_BASE_URL = os.getenv("CLEARPASS_PERPLEXITY_BASE_URL", "").strip()
PERPLEXITY_API_KEY = os.getenv("CLEARPASS_PERPLEXITY_API_KEY", "").strip() or None
PERPLEXITY_DEFAULT_MODEL = os.getenv(
    "CLEARPASS_PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online"
)

OLLAMA_BASE_URL = os.getenv("CLEARPASS_OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = os.getenv("CLEARPASS_OLLAMA_MODEL", "llama3.1")
OLLAMA_CLOUD_BASE_URL = os.getenv("CLEARPASS_OLLAMA_CLOUD_BASE_URL", "").strip()
OLLAMA_CLOUD_DEFAULT_MODEL = os.getenv(
    "CLEARPASS_OLLAMA_CLOUD_MODEL", OLLAMA_DEFAULT_MODEL
)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
KB_SOURCE_DIR = Path(
    os.getenv("CLEARPASS_KB_SOURCE_DIR", BACKEND_ROOT / "data" / "knowledge_base")
)
KB_INDEX_DIR = Path(os.getenv("CLEARPASS_KB_DIR", BACKEND_ROOT / "data" / "kb"))
KB_INDEX_PATH = Path(os.getenv("CLEARPASS_KB_INDEX_PATH", KB_INDEX_DIR / "index.faiss"))
KB_META_PATH = Path(os.getenv("CLEARPASS_KB_META_PATH", KB_INDEX_DIR / "metadata.json"))

KB_PROVIDER = os.getenv("CLEARPASS_KB_PROVIDER", "auto").strip().lower()
SUPABASE_URL = os.getenv("CLEARPASS_SUPABASE_URL", "").strip() or None
SUPABASE_KEY = os.getenv("CLEARPASS_SUPABASE_KEY", "").strip() or None
SUPABASE_TABLE = os.getenv("CLEARPASS_SUPABASE_TABLE", "immigration_knowledge_base")
SUPABASE_MATCH_RPC = os.getenv(
    "CLEARPASS_SUPABASE_MATCH_RPC", "match_immigration_documents"
).strip()

EMBEDDING_MODEL = os.getenv("CLEARPASS_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
KB_EMBEDDING_MODEL = os.getenv(
    "CLEARPASS_KB_EMBEDDING_MODEL", "text-embedding-3-small"
)
RETRIEVAL_TOP_K = int(os.getenv("CLEARPASS_RETRIEVAL_TOP_K", "5"))
KB_CHUNK_SIZE = int(os.getenv("CLEARPASS_KB_CHUNK_SIZE", "1200"))
KB_CHUNK_OVERLAP = int(os.getenv("CLEARPASS_KB_CHUNK_OVERLAP", "200"))
KB_QUERY_MAX_CHARS = int(os.getenv("CLEARPASS_KB_QUERY_MAX_CHARS", "4000"))

ENABLE_TENANTS = _parse_bool(os.getenv("CLEARPASS_ENABLE_TENANTS", "false"))
TENANT_CONFIG_PATH = Path(
    os.getenv("CLEARPASS_TENANT_CONFIG_PATH", BACKEND_ROOT / "data" / "tenants.json")
)
TENANT_HEADER_ID = os.getenv("CLEARPASS_TENANT_HEADER_ID", "X-Tenant-Id")
TENANT_HEADER_TOKEN = os.getenv("CLEARPASS_TENANT_HEADER_TOKEN", "X-Tenant-Token")
ENABLE_METRICS = _parse_bool(os.getenv("CLEARPASS_ENABLE_METRICS", "false"))
ACCURACY_REPORT_PATH = Path(
    os.getenv("CLEARPASS_ACCURACY_REPORT_PATH", BACKEND_ROOT / "data" / "eval" / "last_run.json")
)
ENABLE_REVIEW_QUEUE = _parse_bool(os.getenv("CLEARPASS_ENABLE_REVIEW_QUEUE", "false"))
REVIEW_ADMIN_TOKEN = os.getenv("CLEARPASS_REVIEW_ADMIN_TOKEN", "").strip() or None
REVIEW_QUEUE_TABLE = os.getenv("CLEARPASS_REVIEW_QUEUE_TABLE", "review_queue").strip()
