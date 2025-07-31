from fastapi_template.infrastructure.repositories import RedisRepository


class JwtTokenBlacklist(RedisRepository):
    async def has_blacklisted(self, token_jti: str) -> bool: ...

    async def add_blacklisted(self, token_jti: str) -> None: ...

    async def iter_token_blacklist(
        self,
        *,
        start: int = 0,
        end: int = -1,
    ) -> list[str]: ...


"""
 {
            "sub": str(user_id),
            "email": email,
            "jti": str(token_id),
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": self._settings.jwt_issuer,
            "aud": self._settings.jwt_audience,
            self._TOKEN_TYPE_CLAIM: TokenType.ACCESS.value,
            self._FINGERPRINT_CLAIM: fingerprint_hash,
        }

         options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                },
            )

"""
