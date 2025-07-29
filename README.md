# FastAPI Template

This repository contains a FastAPI backend template packed with the utilities and features I use when creating production grade APIs.

## Disclaimer

This template is a **work in progress** and not production ready yet, feel free to look around and see the approach I use for creating backends
/ APIs with FastAPI.

## Features

- **Session ID based authentication**: Secure session management using Redis and digital signatures.
- **Role-based access control**: Fine-grained permissions for different user roles.
- **User management**: Create, update, and delete users with role assignments.
- **Authentication**: Secure login and logout endpoints with session management.
- **SQLAlchemy Integration**: ORM for database interactions
  - by default SQLite is used, since it's the easiest to set up but since SQLite is very limited
    especially in the context of concurrency, async and performance you should change the database
    to Postgres or MySQL
- **Redis Integration**: Used for session management and caching via `redis[hiredis]` a C extension
  for Redis that provides better performance.
- **Msgspec JSON Serialization**: Fast and efficient JSON serialization
- **Pagination**: Built-in support for paginated responses and query parameters.
- **Database Repository Pattern**: Abstracts database operations for cleaner code with an existing
  interface ready to use.
- **Middleware**: Includes CORS, Access logging and exception handling & logging middleware.
- **API Routes**: Existing api routes for authentication and user management.

## Authentication

Authentication differs from the traditional JWT Token apporach used in most FastAPI tutorials due to the security and session highjacking risks.

### JWT Security Risks

- **Session Hijacking**: JWTs are often stored in local storage or cookies, making them vulnerable to XSS attacks.
- **Token Expiry**: JWTs typically have a fixed expiration time, which can lead to issues if the token is compromised before it expires.
- **Revocation Difficulties**: Once a JWT is issued, it cannot be easily revoked, leading to potential security risks if a token is compromised.
- **Algorithm Vulnerabilities**: JWTs are signed with a known list of algorithms, and once an attacker knows the algorithm, it becomes easier for them
  to forge tokens, or view the contents of the token client side.

I noticed a lack of FastAPI support for comprehensive production grade Session ID based authentication implementations, so I created my own. It uses Redis and digital signatures to securely manage user sessions.

### Session Id Auth Flow

### The client sends a successful login request

1. Server generates a hex for the session ID that is then mapped the information of said token in Redis, before the ID is returned to the client it is signed using `itsdangerous` using the secret key.

   - The Session ID is then set to expire within the next hour.

2. The response is then sent to the client which contains the Session ID in the response body, where your frontend can the store this in a cookie.

### The client accesses a protected route

1. The request is sent in the `Authorization` header with the value `Bearer <session_id>`.

2. The server checks if the signature is valid and removes it if so.

3. The server retrieves the raw session ID from Redis and loads the session information before then verifying
   - A. The user it corresponds to still exists by checking the user ID
   - B. The role of the user is valid for the route being accessed
   - C. Has the max session lifetime been reached? If so, the session is revoked and
     the user must log in again.

_The session ID will not exist if it has expired (i.e User hasn't sent a request in the last hour) or if the user has logged out._

3. If the session is valid, the set expiration of the session ID in redis is extended by another hour.

4. The server then returns the response to the client.

### An attacker compromises uses the session Id of a user

1. The request is sent in the `Authorization` header with the value `Bearer <session_id>`.
2. The server checks if the signature is valid and removes it if so.
3. The server retrieves the raw session ID from Redis and loads the session information
4. The session information of the user who created it (e.g User Agent) is compared to the request
   to determine if this the same client
5. It's not and the server revokes the session ID, returning a 403 Forbidden response to the client.


