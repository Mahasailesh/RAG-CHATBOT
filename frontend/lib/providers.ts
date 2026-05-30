type ProviderOption = { value: string; label: string };

const DEFAULT_PROVIDERS = [
  "gemini",
  "openai",
  "anthropic",
  "ollama",
  "ollama_cloud",
  "openai_compatible",
  "groq",
  "together",
  "mistral",
  "perplexity"
];

const LABELS: Record<string, string> = {
  gemini: "Gemini",
  openai: "OpenAI",
  anthropic: "Anthropic",
  ollama: "Ollama (Local)",
  ollama_cloud: "Ollama Cloud",
  openai_compatible: "OpenAI-compatible",
  groq: "Groq",
  together: "Together",
  mistral: "Mistral",
  perplexity: "Perplexity"
};

function parseProviders(raw: string | undefined): string[] {
  if (!raw) {
    return DEFAULT_PROVIDERS;
  }
  return raw
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

export function getProviderOptions(): ProviderOption[] {
  const raw = process.env.NEXT_PUBLIC_ALLOWED_PROVIDERS;
  const providers = parseProviders(raw);
  const unique = Array.from(new Set(providers));
  return unique.map((value) => ({
    value,
    label: LABELS[value] ?? value.replace(/_/g, " ").toUpperCase()
  }));
}
