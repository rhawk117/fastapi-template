from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Self

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def read_file_bytes(file_path: Path) -> bytes:
    if not file_path.exists():
        raise FileNotFoundError(f'Key file {file_path} does not exist.')

    with file_path.open('rb') as key_file:
        return key_file.read()


@dataclass(slots=True, frozen=True, kw_only=True)
class AsymmetricKeyPair:
    """
    Represents an asymmetric key pair (private and public keys)
    with cached single computed properties for the keys.
    """

    _private_key: rsa.RSAPrivateKey
    _public_key: rsa.RSAPublicKey

    @classmethod
    def from_key_files(
        cls,
        private_key_file: Path,
        public_key_file: Path,
        *,
        private_key_password: str | None = None,
    ) -> Self:
        private_key_data = read_file_bytes(private_key_file)
        public_key_data = read_file_bytes(public_key_file)
        password = (
            None
            if private_key_password is None
            else private_key_password.encode('utf-8')
        )

        private_key: rsa.RSAPrivateKey = serialization.load_pem_private_key(
            private_key_data, password=password
        )  # type: ignore
        public_key: rsa.RSAPublicKey = serialization.load_pem_public_key(
            public_key_data
        )  # type: ignore

        return cls(_private_key=private_key, _public_key=public_key)

    @cached_property
    def private_key(self) -> bytes:
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    @cached_property
    def public_key(self) -> bytes:
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
