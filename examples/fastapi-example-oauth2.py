# This example demonstrates how use Dante to implement OAuth2 for FastAPI.
#
# To run this example, you need to install FastAPI:
#
#   $ pip install fastapi[standard]
#
# Then, you can run the FastAPI server:
#
#   $ cd examples/
#   $ fastapi dev fastapi-example-oauth2.py
#
# And visit http://localhost:8000/docs to interact with the API.

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi_auth import (
    User,
    create_user,
    get_current_user_oauth2,
    init,
    oauth2_login_flow,
)
from pydantic import BaseModel

from dante import Dante

app = FastAPI()
db = Dante("users.db", check_same_thread=False)
users = init(db)


class SignupRequest(BaseModel):
    username: str
    password: str


@app.post("/token")
async def login(response: dict = Depends(oauth2_login_flow)):
    return response


@app.get("/me")
def read_current_user(current_user: Annotated[User, Depends(get_current_user_oauth2)]):
    return current_user


@app.post("/signup")
def signup(req: SignupRequest):
    return create_user(req.username, req.password, include_token=True)
