"""
Secrets Detection Patterns

Detect sensitive credentials that should ALWAYS be redacted:
- API keys (AWS, GitHub, OpenAI, etc.)
- Private keys (RSA, EC, SSH)
- Authentication tokens
- Database connection strings
- OAuth tokens

Priority: 100 (ALWAYS redact)
"""

import re
from typing import List, Tuple

# Secrets patterns - ALL have priority 100 (always redact)
SECRETS_PATTERNS = [
    # AWS Access Keys
    (r"AKIA[0-9A-Z]{16}", "AWS_ACCESS_KEY", 100, "aws_access_key"),
    (r"(?:aws_secret_access_key|aws_session_token)\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
     "AWS_SECRET_KEY", 100, "aws_secret"),

    # Private Keys
    (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "PRIVATE_KEY", 100, "private_key"),
    (r"-----BEGIN CERTIFICATE-----", "CERTIFICATE", 95, "certificate"),

    # GitHub Personal Access Tokens
    (r"gh[pousr]_[A-Za-z0-9]{36,}", "GITHUB_TOKEN", 100, "github_pat"),
    (r"github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}", "GITHUB_TOKEN", 100, "github_pat_new"),

    # OpenAI API Keys
    (r"sk-[A-Za-z0-9]{48}", "OPENAI_API_KEY", 100, "openai_key"),
    (r"sk-proj-[A-Za-z0-9]{48}", "OPENAI_PROJECT_KEY", 100, "openai_proj_key"),

    # Anthropic API Keys
    (r"sk-ant-[A-Za-z0-9\-]{95,}", "ANTHROPIC_API_KEY", 100, "anthropic_key"),

    # Generic API Keys (common patterns)
    (r"(?:api[_-]?key|apikey|api_secret)\s*[:=]\s*['\"]([A-Za-z0-9_\-]{20,})['\"]",
     "API_KEY", 95, "api_key_generic"),

    # Bearer Tokens
    (r"(?:Authorization|Bearer)\s*:\s*Bearer\s+([A-Za-z0-9\-._~+/]+=*)",
     "BEARER_TOKEN", 100, "bearer_token"),

    # Database Connection Strings
    (r"(?:postgres|mysql|mongodb)://[^:]+:[^@]+@[^/]+/\w+",
     "DATABASE_CONNECTION", 100, "db_connection"),
    (r"(?:Server|Data Source)=.+;(?:User ID|UID)=.+;(?:Password|PWD)=.+;",
     "DATABASE_CONNECTION", 100, "db_connection_mssql"),

    # OAuth Tokens
    (r"(?:oauth|access)_token\s*[:=]\s*['\"]?([A-Za-z0-9\-._~+/]+=*)['\"]?",
     "OAUTH_TOKEN", 100, "oauth_token"),

    # Stripe Keys
    (r"(?:sk|pk)_(?:live|test)_[0-9a-zA-Z]{24,}",
     "STRIPE_KEY", 100, "stripe_key"),

    # Slack Tokens
    (r"xox[pboa]-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24,}",
     "SLACK_TOKEN", 100, "slack_token"),

    # JWT Tokens (standard format)
    (r"eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_.+/=]+",
     "JWT_TOKEN", 95, "jwt_token"),

    # Google API Keys
    (r"AIza[0-9A-Za-z\-_]{35}",
     "GOOGLE_API_KEY", 100, "google_api_key"),

    # Heroku API Keys
    (r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
     "UUID_TOKEN", 90, "uuid_token"),

    # NPM Tokens
    (r"npm_[A-Za-z0-9]{36}",
     "NPM_TOKEN", 100, "npm_token"),

    # PyPI Tokens
    (r"pypi-AgEIcHlwaS5vcmc[A-Za-z0-9\-_]{70,}",
     "PYPI_TOKEN", 100, "pypi_token"),

    # SSH Private Key Indicators
    (r"(?:id_rsa|id_dsa|id_ecdsa|id_ed25519)[\s\S]*?-----BEGIN",
     "SSH_PRIVATE_KEY", 100, "ssh_key"),

    # Environment Variables with Secrets
    (r"(?:SECRET|PASSWORD|TOKEN|KEY|PRIVATE)=['\"]?([A-Za-z0-9\-._~+/]+=*)['\"]?",
     "ENV_SECRET", 90, "env_secret"),
]


def get_secrets_patterns() -> List[Tuple[str, str, int, str]]:
    """
    Get all secrets detection patterns.

    Returns:
        List of (regex_pattern, entity_type, priority, pattern_name)
    """
    return SECRETS_PATTERNS


def validate_aws_key(key: str) -> bool:
    """
    Validate AWS access key format.

    AWS Access Keys always start with AKIA and are 20 characters.
    """
    return len(key) == 20 and key.startswith("AKIA")


def validate_github_token(token: str) -> bool:
    """
    Validate GitHub personal access token format.

    Old format: ghp_, gho_, ghu_, ghs_ + 36 chars
    New format: github_pat_ + 22 chars + _ + 59 chars
    """
    if token.startswith("gh"):
        prefix = token[:4]
        if prefix in ["ghp_", "gho_", "ghu_", "ghs_"]:
            return len(token) == 40
    if token.startswith("github_pat_"):
        parts = token.split("_")
        return len(parts) == 3 and len(parts[2]) == 22 and len(parts[-1]) == 59

    return False


def is_likely_test_secret(value: str) -> bool:
    """
    Check if a detected secret is likely a test/placeholder value.

    Returns:
        True if value appears to be a test secret
    """
    test_indicators = [
        "example",
        "test",
        "dummy",
        "placeholder",
        "sample",
        "fake",
        "mock",
        "xxxxx",
        "yyyyy",
        "aaaaa",
        "00000",
    ]

    value_lower = value.lower()
    return any(indicator in value_lower for indicator in test_indicators)


# Example usage
if __name__ == "__main__":
    test_texts = [
        "My AWS key is AKIAIOSFODNN7EXAMPLE",
        "sk-ant-api03-abc123...",
        "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    ]

    for text in test_texts:
        print(f"\nTesting: {text[:50]}...")
        for pattern, entity_type, priority, name in SECRETS_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                print(f"  ✓ Detected {entity_type} (priority {priority}): {name}")
