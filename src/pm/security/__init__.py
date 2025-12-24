"""Security module for PersonalManager.

Provides secrets management.
"""

from .secrets import SecretsManager, SecretType

__all__ = [
    'SecretsManager',
    'SecretType'
]

__version__ = '1.0.0'
