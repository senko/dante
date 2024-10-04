# This example demonstrates how use Dante to implement basic auth for FastAPI.
#
# To run this example, you need to install FastAPI:
#
#   $ pip install fastapi[standard]
#
# Then, you can run the FastAPI server:
#
#   $ cd examples/
#   $ fastapi dev fastapi-example-basic-auth.py
#
# And visit http://localhost:8000/docs to interact with the API.

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi_auth import User, create_user, get_current_user_basic, init
from pydantic import BaseModel

from dante import Dante

app = FastAPI()
db = Dante("users.db", check_same_thread=False)
users = init(db)


class SignupRequest(BaseModel):
    username: str
    password: str


@app.get("/me")
def read_current_user(current_user: Annotated[User, Depends(get_current_user_basic)]):
    return current_user


@app.post("/signup")
def signup(req: SignupRequest):
    return create_user(req.username, req.password)
