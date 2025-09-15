"""Secure secrets management for PersonalManager.

Provides encrypted storage and retrieval of sensitive data including
API keys, passwords, tokens, and configuration secrets.
"""

import base64
import json
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List
from uuid import uuid4


class SecretType(Enum):
    """Types of secrets managed by the system."""
    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    CERTIFICATE = "certificate"
    PRIVATE_KEY = "private_key"
    DATABASE_CREDENTIAL = "database_credential"
    ENCRYPTION_KEY = "encryption_key"
    WEBHOOK_SECRET = "webhook_secret"
    OAUTH_SECRET = "oauth_secret"


@dataclass
class Secret:
    """Secret data structure with metadata."""
    id: str
    name: str
    type: SecretType
    value: str  # Encrypted value
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    rotation_period: Optional[timedelta]
    last_rotated: Optional[datetime]
    tags: Dict[str, str]
    metadata: Dict[str, Any]

    @property
    def is_expired(self) -> bool:
        """Check if secret has expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    @property
    def needs_rotation(self) -> bool:
        """Check if secret needs rotation."""
        if self.rotation_period and self.last_rotated:
            next_rotation = self.last_rotated + self.rotation_period
            return datetime.utcnow() > next_rotation
        return False


class SecretsManager:
    """Secure secrets management with encryption at rest."""

    def __init__(self, vault_path: Optional[Path] = None,
                 master_key_path: Optional[Path] = None):
        """Initialize secrets manager.

        Args:
            vault_path: Path to encrypted secrets vault
            master_key_path: Path to master encryption key
        """
        self.vault_path = vault_path or Path.home() / ".pm" / "secrets.vault"
        self.master_key_path = master_key_path or Path.home() / ".pm" / ".master_key"
        self.cipher = self._initialize_encryption()
        self.secrets: Dict[str, Secret] = {}
        self._load_vault()

    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption cipher with master key.

        Returns:
            Fernet cipher for encryption/decryption
        """
        if self.master_key_path.exists():
            # Load existing master key
            with open(self.master_key_path, 'rb') as f:
                key = f.read()
        else:
            # Generate new master key
            key = self._generate_master_key()
            self.master_key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.master_key_path, 'wb') as f:
                f.write(key)
            # Restrict access to owner only
            self.master_key_path.chmod(0o600)

        return Fernet(key)

    def _generate_master_key(self) -> bytes:
        """Generate a new master encryption key.

        Returns:
            Master encryption key
        """
        # Use PBKDF2 for key derivation
        password = os.urandom(32)  # Random password
        salt = os.urandom(16)  # Random salt

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def _load_vault(self):
        """Load and decrypt secrets vault."""
        if self.vault_path.exists():
            try:
                with open(self.vault_path, 'rb') as f:
                    encrypted_data = f.read()

                # Decrypt vault
                decrypted_data = self.cipher.decrypt(encrypted_data)
                vault_data = json.loads(decrypted_data.decode())

                # Load secrets
                for secret_data in vault_data.get('secrets', []):
                    secret = self._deserialize_secret(secret_data)
                    self.secrets[secret.id] = secret

            except Exception as e:
                print(f"Warning: Failed to load secrets vault: {e}")
                # Initialize empty vault on error
                self.secrets = {}

    def _save_vault(self):
        """Encrypt and save secrets vault."""
        try:
            # Serialize secrets
            vault_data = {
                'version': '1.0.0',
                'updated_at': datetime.utcnow().isoformat(),
                'secrets': [self._serialize_secret(s) for s in self.secrets.values()]
            }

            # Encrypt vault
            data = json.dumps(vault_data).encode()
            encrypted_data = self.cipher.encrypt(data)

            # Save to file
            self.vault_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.vault_path, 'wb') as f:
                f.write(encrypted_data)

            # Restrict access
            self.vault_path.chmod(0o600)

        except Exception as e:
            raise RuntimeError(f"Failed to save secrets vault: {e}")

    def _serialize_secret(self, secret: Secret) -> Dict[str, Any]:
        """Serialize secret for storage."""
        return {
            'id': secret.id,
            'name': secret.name,
            'type': secret.type.value,
            'value': secret.value,
            'description': secret.description,
            'created_at': secret.created_at.isoformat(),
            'updated_at': secret.updated_at.isoformat(),
            'expires_at': secret.expires_at.isoformat() if secret.expires_at else None,
            'rotation_period': secret.rotation_period.total_seconds() if secret.rotation_period else None,
            'last_rotated': secret.last_rotated.isoformat() if secret.last_rotated else None,
            'tags': secret.tags,
            'metadata': secret.metadata
        }

    def _deserialize_secret(self, data: Dict[str, Any]) -> Secret:
        """Deserialize secret from storage."""
        return Secret(
            id=data['id'],
            name=data['name'],
            type=SecretType(data['type']),
            value=data['value'],
            description=data.get('description'),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            rotation_period=timedelta(seconds=data['rotation_period']) if data.get('rotation_period') else None,
            last_rotated=datetime.fromisoformat(data['last_rotated']) if data.get('last_rotated') else None,
            tags=data.get('tags', {}),
            metadata=data.get('metadata', {})
        )

    def store_secret(self,
                    name: str,
                    value: str,
                    secret_type: SecretType,
                    description: Optional[str] = None,
                    expires_in: Optional[timedelta] = None,
                    rotation_period: Optional[timedelta] = None,
                    tags: Optional[Dict[str, str]] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Secret:
        """Store a new secret securely.

        Args:
            name: Secret name/identifier
            value: Secret value to encrypt
            secret_type: Type of secret
            description: Optional description
            expires_in: Optional expiration period
            rotation_period: Optional rotation period
            tags: Optional tags for organization
            metadata: Optional metadata

        Returns:
            Created secret object
        """
        # Encrypt the secret value
        encrypted_value = self.cipher.encrypt(value.encode()).decode()

        # Create secret object
        secret = Secret(
            id=str(uuid4()),
            name=name,
            type=secret_type,
            value=encrypted_value,
            description=description,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + expires_in if expires_in else None,
            rotation_period=rotation_period,
            last_rotated=datetime.utcnow() if rotation_period else None,
            tags=tags or {},
            metadata=metadata or {}
        )

        # Store and save
        self.secrets[secret.id] = secret
        self._save_vault()

        return secret

    def get_secret(self, secret_id: str) -> Optional[str]:
        """Retrieve and decrypt a secret.

        Args:
            secret_id: Secret ID

        Returns:
            Decrypted secret value or None if not found/expired
        """
        secret = self.secrets.get(secret_id)
        if not secret:
            return None

        # Check expiration
        if secret.is_expired:
            print(f"Warning: Secret {secret_id} has expired")
            return None

        # Check rotation
        if secret.needs_rotation:
            print(f"Warning: Secret {secret_id} needs rotation")

        # Decrypt and return
        try:
            decrypted = self.cipher.decrypt(secret.value.encode())
            return decrypted.decode()
        except Exception as e:
            print(f"Error decrypting secret {secret_id}: {e}")
            return None

    def get_secret_by_name(self, name: str) -> Optional[str]:
        """Retrieve secret by name.

        Args:
            name: Secret name

        Returns:
            Decrypted secret value or None
        """
        for secret in self.secrets.values():
            if secret.name == name:
                return self.get_secret(secret.id)
        return None

    def update_secret(self, secret_id: str, new_value: str) -> bool:
        """Update an existing secret.

        Args:
            secret_id: Secret ID
            new_value: New secret value

        Returns:
            True if updated successfully
        """
        secret = self.secrets.get(secret_id)
        if not secret:
            return False

        # Encrypt new value
        encrypted_value = self.cipher.encrypt(new_value.encode()).decode()

        # Update secret
        secret.value = encrypted_value
        secret.updated_at = datetime.utcnow()
        if secret.rotation_period:
            secret.last_rotated = datetime.utcnow()

        # Save changes
        self._save_vault()
        return True

    def rotate_secret(self, secret_id: str, new_value: str) -> bool:
        """Rotate a secret with audit trail.

        Args:
            secret_id: Secret ID
            new_value: New secret value

        Returns:
            True if rotated successfully
        """
        secret = self.secrets.get(secret_id)
        if not secret:
            return False

        # Store rotation in metadata
        if 'rotation_history' not in secret.metadata:
            secret.metadata['rotation_history'] = []

        secret.metadata['rotation_history'].append({
            'rotated_at': datetime.utcnow().isoformat(),
            'previous_hash': hashlib.sha256(secret.value.encode()).hexdigest()
        })

        # Update secret
        return self.update_secret(secret_id, new_value)

    def delete_secret(self, secret_id: str) -> bool:
        """Delete a secret permanently.

        Args:
            secret_id: Secret ID

        Returns:
            True if deleted successfully
        """
        if secret_id in self.secrets:
            del self.secrets[secret_id]
            self._save_vault()
            return True
        return False

    def list_secrets(self,
                    secret_type: Optional[SecretType] = None,
                    tags: Optional[Dict[str, str]] = None,
                    include_expired: bool = False) -> List[Dict[str, Any]]:
        """List secrets with filters.

        Args:
            secret_type: Filter by type
            tags: Filter by tags
            include_expired: Include expired secrets

        Returns:
            List of secret metadata (without values)
        """
        results = []

        for secret in self.secrets.values():
            # Filter by type
            if secret_type and secret.type != secret_type:
                continue

            # Filter by expiration
            if not include_expired and secret.is_expired:
                continue

            # Filter by tags
            if tags:
                if not all(secret.tags.get(k) == v for k, v in tags.items()):
                    continue

            # Add to results (without sensitive value)
            results.append({
                'id': secret.id,
                'name': secret.name,
                'type': secret.type.value,
                'description': secret.description,
                'created_at': secret.created_at.isoformat(),
                'updated_at': secret.updated_at.isoformat(),
                'expires_at': secret.expires_at.isoformat() if secret.expires_at else None,
                'is_expired': secret.is_expired,
                'needs_rotation': secret.needs_rotation,
                'tags': secret.tags
            })

        return results

    def check_expiring_secrets(self, days: int = 7) -> List[Dict[str, Any]]:
        """Check for secrets expiring soon.

        Args:
            days: Number of days to look ahead

        Returns:
            List of expiring secrets
        """
        expiring = []
        threshold = datetime.utcnow() + timedelta(days=days)

        for secret in self.secrets.values():
            if secret.expires_at and secret.expires_at <= threshold:
                expiring.append({
                    'id': secret.id,
                    'name': secret.name,
                    'type': secret.type.value,
                    'expires_at': secret.expires_at.isoformat(),
                    'days_remaining': (secret.expires_at - datetime.utcnow()).days
                })

        return expiring

    def check_rotation_needed(self) -> List[Dict[str, Any]]:
        """Check for secrets needing rotation.

        Returns:
            List of secrets needing rotation
        """
        needing_rotation = []

        for secret in self.secrets.values():
            if secret.needs_rotation:
                needing_rotation.append({
                    'id': secret.id,
                    'name': secret.name,
                    'type': secret.type.value,
                    'last_rotated': secret.last_rotated.isoformat() if secret.last_rotated else None,
                    'rotation_period': secret.rotation_period.total_seconds() if secret.rotation_period else None
                })

        return needing_rotation

    def export_backup(self, password: str) -> bytes:
        """Export encrypted backup of all secrets.

        Args:
            password: Password for backup encryption

        Returns:
            Encrypted backup data
        """
        # Generate backup key from password
        salt = os.urandom(16)
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        backup_cipher = Fernet(key)

        # Prepare backup data
        backup_data = {
            'version': '1.0.0',
            'created_at': datetime.utcnow().isoformat(),
            'secrets': [self._serialize_secret(s) for s in self.secrets.values()]
        }

        # Encrypt backup
        data = json.dumps(backup_data).encode()
        encrypted_backup = backup_cipher.encrypt(data)

        # Include salt for key derivation
        return salt + encrypted_backup

    def import_backup(self, backup_data: bytes, password: str) -> bool:
        """Import encrypted backup of secrets.

        Args:
            backup_data: Encrypted backup data
            password: Password for backup decryption

        Returns:
            True if import successful
        """
        try:
            # Extract salt and encrypted data
            salt = backup_data[:16]
            encrypted_data = backup_data[16:]

            # Derive key from password
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            backup_cipher = Fernet(key)

            # Decrypt backup
            decrypted_data = backup_cipher.decrypt(encrypted_data)
            backup = json.loads(decrypted_data.decode())

            # Import secrets
            for secret_data in backup.get('secrets', []):
                secret = self._deserialize_secret(secret_data)
                self.secrets[secret.id] = secret

            # Save imported secrets
            self._save_vault()
            return True

        except Exception as e:
            print(f"Failed to import backup: {e}")
            return False