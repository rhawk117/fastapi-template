import functools
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from fastapi_template.core import config


@dataclass(slots=True, kw_only=True, frozen=True)
class AsymmetricKeyPair:
    private_key_file: Path
    public_key_file: Path
    password: bytes | None = None

    def _read_key_file(self, file_path: Path) -> bytes:
        if not file_path.exists():
            raise FileNotFoundError(f'Key file {file_path} does not exist.')
        with file_path.open('rb') as key_file:
            return key_file.read()

    @functools.cached_property
    def private_key(self) -> rsa.RSAPrivateKey:
        private_key_data = self._read_key_file(self.private_key_file)
        return serialization.load_pem_private_key(
            private_key_data,
            password=self.password,  # type: ignore
        )

    @functools.cached_property
    def public_key(self) -> rsa.RSAPublicKey:
        public_key_data = self._read_key_file(self.public_key_file)
        return serialization.load_pem_public_key(public_key_data)  # type: ignore


def _create_jwt_pair() -> AsymmetricKeyPair:
    secrets = config.get_secrets()
    return AsymmetricKeyPair(
        private_key_file=secrets.private_key_path(),
        public_key_file=secrets.public_key_path(),
    )


JWTKeys = _create_jwt_pair()
