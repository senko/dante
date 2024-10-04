# Dante-backed user authentication for FastAPI
#
# Provides a simple user authentication system with a simple User
# model, and implements basic and OAuth2 password flows. Copy and
# adapt as needed for your project.
#
# For usage, check fastapi-example-basic-auth.py
# and fastapi-example-oauth2.py.

from __future__ import annotations

from datetime import datetime
from hashlib import sha512
from typing import Annotated, Optional
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from passlib.hash import pbkdf2_sha512
from pydantic import BaseModel, Field

from dante.sync import Collection, Dante

users: Collection


class User(BaseModel):
    """ "
    User model for authentication.

    Password is stored hashed (use `User.set_password()`) and is never
    serialized back to the client.
    """

    username: str
    password_hash: str = ""
    created_at: datetime
    is_active: bool = True
    token: Optional[str] = None

    def set_password(self, password: str):
        """
        Set the user's password.

        Note that this only updates the `password_hash` field on
        the object, and doesn't actually save/update the object in the
        database.

        :param password: Password to hash and store
        """
        self.password_hash = hash_pwd(password)


class CurrentUser(User):
    """
    User model for the current user, suitable to return to the API client.

    This excludes the password hash field so it's not included
    in the response to the client. Note that you don't want to save this
    to the database, otherwise you'll reset (remove) the user's password.
    """

    password_hash: str = Field("", exclude=True)


# Support for HTTP Basic auth with username/password in Authorization header
basic_security = HTTPBasic()
# Support for OAuth2 password flow with bearer token in Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def init(db: Dante) -> Collection:
    """
    Initialize the Users collection in the database.

    :param db: Dante instance
    :return: Users collection
    """
    global users
    users = db[User]
    return users


def hash_pwd(password: str) -> str:
    """
    Hash a password using PBKDF2 with SHA-512.

    Internal method, should only be used in fastapi_auth module.

    :param password: Password to hash
    :return: Hashed password
    """
    return pbkdf2_sha512.hash(password)


def verify_pwd(password: str, hash: str) -> bool:
    """
    Verify a password against a hash using PBKDF2 with SHA-512.

    Internal method, should only be used in fastapi_auth module.

    :param password: Password to verify
    :param hash: Hashed password
    :return: True if the password matches the hash, False otherwise
    """
    return pbkdf2_sha512.verify(password, hash)


def create_user(username: str, password: str, include_token=False) -> CurrentUser:
    """
    Create a new user with the given username and password.

    Caveat: this simple implementation is vulnerable to race conditions
    in which many users with the same username are created at the
    same time. A full implementation would use a database transaction
    to ensure check and insert are atomic.

    :param username: Username
    :param password: Password
    :param include_token: Whether to include a token in the response
    :return: Newly created user
    """
    if users.find_one(username=username):
        raise ValueError("User already exists")
    user = User(username=username, created_at=datetime.now())
    user.set_password(password)
    if include_token:
        user.token = sha512(uuid4().bytes).hexdigest()
    users.insert(user)
    return CurrentUser(**user.model_dump())


def get_current_user_basic(
    credentials: HTTPBasicCredentials = Depends(basic_security),
) -> CurrentUser:
    """
    Get current used assuming Basic HTTP auth.

    If there's no current user, raises a 401 Unauthorized exception.

    :param credentials: HTTP Basic credentials dependency from FastAPI
    :return: The current user
    """
    user = users.find_one(username=credentials.username)
    if user is None or not verify_pwd(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return CurrentUser(**user.model_dump())


def get_current_user_oauth2(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CurrentUser:
    """
    Get current user assuming OAuth2 bearer token.

    If there's no current user, raises a 401 Unauthorized exception.

    :param token: OAuth2 bearer token dependency from FastAPI
    :return: The current user
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    user = users.find_one(token=token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    # We don't want the client to see even the hashed password of the user.
    # Note this means that if you just update the user object, it'll set
    # the password to an empty string, effectively locking out the user.
    return CurrentUser(**user.model_dump())


def oauth2_login_flow(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> dict:
    """
    Implementation of the OAuth2 password flow.

    If the user is not found or the password is incorrect, raises a 401
    Unauthorized exception.

    :param form_data: OAuth2 password request form from FastAPI
    :return: OAuth2 access token
    """
    user = users.find_one(username=form_data.username)
    if user is None or not verify_pwd(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    user.token = sha512(uuid4().bytes).hexdigest()
    users.update(user, username=user.username)
    return {"access_token": user.token, "token_type": "bearer"}
