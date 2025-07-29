import os
import secrets
import sys
from pathlib import Path

from cryptography.fernet import Fernet


def create_secrets() -> dict:
    return {
        'SECRET_KEY': secrets.token_urlsafe(32),
        'SIGNATURE_SALT': secrets.token_urlsafe(32),
        'ENCRYPTION_KEY': Fernet.generate_key().decode('utf-8'),
        'ENCRYPTION_SALT': secrets.token_urlsafe(32),
        'REDIS_PASSWORD': secrets.token_urlsafe(32),
    }


def main(output_file: str) -> None:
    os.chdir(Path(__file__).parent.parent)
    secrets_dict = create_secrets()
    secret_str = '\n'.join(f'{key}={value}' for key, value in secrets_dict.items())
    with open(output_file, 'w') as f:
        f.write(secret_str)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python create_env.py <output_file>')
        sys.exit(1)
    output_file = sys.argv[1]
    main(output_file)
