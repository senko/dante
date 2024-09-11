# This example demonstrates how to use Dante with FastAPI.
#
# To run this example, you need to install FastAPI:
#
#   $ pip install fastapi[standard]
#
# Then, you can run the FastAPI server:
#
#   $ cd examples/
#   $ fastapi dev fastapi-example.py
#
# And visit http://localhost:8000/docs to interact with the API.

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from dante import Dante


class Book(BaseModel):
    isbn: str
    title: str
    authors: list[str]
    published_date: date
    summary: Optional[str] = None


app = FastAPI()
db = Dante("books.db", check_same_thread=False)
books = db[Book]


@app.get("/books/")
def list_books() -> list[Book]:
    return books.find_many()


@app.post("/books/", status_code=status.HTTP_201_CREATED)
def create_book(book: Book):
    books.insert(book)
    return book


@app.get("/books/{isbn}")
def get_book(isbn: str):
    book = books.find_one(isbn=isbn)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    return book


@app.put("/books/{isbn}")
def update_book(isbn: str, book: Book):
    n = books.update(book, isbn=isbn)
    if not n:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    return book


@app.delete("/books/{isbn}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(isbn: str):
    n = books.delete(isbn=isbn)
    if not n:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    return {"message": "Book deleted"}
