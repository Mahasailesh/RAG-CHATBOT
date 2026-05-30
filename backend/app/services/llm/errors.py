class ProviderError(Exception):
    pass


class ProviderNotAllowed(ProviderError):
    pass


class ProviderAuthError(ProviderError):
    pass


class ProviderResponseError(ProviderError):
    pass
