from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, TypeVar

from pydantic import BaseModel

TModel = TypeVar("TModel", bound=BaseModel)


class DanteEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for handling datetime and date objects.

    This encoder extends the default JSON encoder to properly serialize
    datetime and date objects by converting them to ISO format strings.
    """

    def default(self, obj: Any) -> str | Any:
        """
        Encode datetime and date objects as ISO format strings.

        :param obj: The object to be encoded.

        :returns: JSON-serializable representation of obj
        """
        if isinstance(obj, datetime) or isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)  # pragma: no cover


class BaseDante(ABC):
    """
    Base class for Dante database operations.

    :param db_name: Name of the database, defaults to in-memory database
    :param auto_commit: Whether to automatically commit transactions, defaults to True
    :param check_same_thread: Whether to check if the same thread is used, defaults to True
    """

    MEMORY = ":memory:"

    def __init__(
        self,
        db_name: str = MEMORY,
        auto_commit: bool = True,
        check_same_thread: bool = True,
    ):
        """
        Initialize the Dante instance.

        :param db_name: Name of the database, defaults to in-memory database
        :param auto_commit: Whether to automatically commit transactions, defaults to True
        :param check_same_thread: Whether to check if the same thread is used, defaults to True

        SQLite by default forbids using the same database connection from multiple threads,
        but in some cases (eg. FastAPI) it may be useful to allow this behavior. To allow
        this, set `check_same_thread` to False.

        """
        self.db_name = db_name
        self.conn: Any | None = None
        self.auto_commit = auto_commit
        self.check_same_thread = check_same_thread

    def __str__(self) -> str:
        """
        Return a string representation of the Dante instance.

        :return: String representation of the instance
        """
        return f'<{self.__class__.__name__}("{self.db_name}")>'

    @abstractmethod
    def get_connection(self):
        """
        Get a connection to the database.

        :return: Database connection object
        """

    @abstractmethod
    def collection(self, name: str, model: TModel | None = None):
        """
        Get a collection from the database.

        :param name: Name of the collection
        :param model: Pydantic model class (if using with Pydantic)

        :return: Collection instance
        """

    def __getitem__(self, name: str | TModel):
        """
        Get a collection using dictionary-like syntax.

        :param name: Name of the collection or a Pydantic model class
        :return: Collection instance
        """
        if isinstance(name, str):
            return self.collection(name)
        elif isinstance(name, type) and issubclass(name, BaseModel):
            return self.collection(name.__name__, name)
        else:
            raise TypeError(
                "Key must be string or Pydantic model class"
            )  # pragma: no cover

    @abstractmethod
    def _maybe_commit(self):
        """
        Commit the current transaction if auto-commit is enabled.
        """

    @abstractmethod
    def commit(self):
        """
        Commit the current transaction (if auto-commit is disabled).

        This method is a no-op if auto-commit is enabled.
        """

    @abstractmethod
    def close(self):
        """
        Close the database connection.

        This method should be called when the database is no longer needed.
        """


class BaseCollection(ABC):
    """
    Base class for collection operations in the Dante database.

    This class provides methods for interacting with collections in the database,
    including serialization and deserialization of data, and query building for
    find, update and delete methods.

    :param name: Name of the collection
    :param db: Dante instance representing the database
    :param model: Optional Pydantic model class for data validation and serialization
    """

    def __init__(self, name: str, db: BaseDante, model: TModel | None = None):
        """
        Initialize the BaseCollection instance.

        :param name: Name of the collection
        :param db: BaseDante instance representing the database
        :param model: Optional Pydantic model class for data validation and serialization
        """
        self.name = name
        self.db = db
        self.model = model

    def __str__(self) -> str:
        """
        Return a string representation of the BaseCollection instance.

        :return: String representation of the instance
        """
        return f'<{self.__class__.__name__}("{self.db.db_name}/{self.name}")>'

    def _to_json(self, data: dict | TModel) -> str:
        """
        Internal method to serialize data to JSON before saving.

        :param data: Data or Pydantic object to serialize
        :return: JSON-serialized data
        """
        if self.model and isinstance(data, BaseModel):
            return data.model_dump_json()
        else:
            return json.dumps(data, cls=DanteEncoder)

    def _from_json(self, json_text: str) -> dict | TModel:
        """
        Internal method to parse JSON data after loading.

        :param json_text: Raw JSON data to parse
        :return: Deserialized data as dictionary or Pydantic model
        """
        data = json.loads(json_text)
        return self.model(**data) if self.model and callable(self.model) else data

    def _build_query(_self, _limit: int | None, /, **kwargs: Any) -> tuple[str, list]:
        """
        Internal method to create an SQL WHERE/LIMIT clauses.

        Builds the query from key/value pairs with optional limit.

        :param _limit: Optional LIMIT clause
        :param kwargs: key/value pairs to search for
        :return: fragments of query to prepare, with corresponding values

        """
        values = []
        if kwargs:
            query_parts = []
            for key, value in kwargs.items():
                key = "$." + key.replace("__", ".")
                query_parts.append("data->>? = ?")
                values.extend([key, value])
            query = " WHERE " + " AND ".join(query_parts)
        else:
            query = ""

        if _limit:
            query += " LIMIT ?"
            values.append(_limit)

        return query, values

    def _build_set_clause(_self, **kwargs: Any) -> tuple[str, list]:
        """
        Internal method to create an SQL SET clause.

        Builds the SET clause from key/value pairs.

        :param kwargs: key/value pairs to set
        :return: fragments of query to prepare, with corresponding values
        """
        clause_parts = []
        values = []
        for key, value in kwargs.items():
            key = key.replace("__", ".")
            clause_parts.append("?, ?")
            values.extend(["$." + key, value])
        clause = "SET data = json_set(data, " + ", ".join(clause_parts) + ")"

        return clause, values

    @abstractmethod
    def insert(self, data: dict | TModel):
        """
        Insert data into the collection.

        :param data: Data to insert
        """

    @abstractmethod
    def find_many(
        _self,
        _limit: int | None = None,
        /,
        **kwargs: Any,
    ):
        """
        Find documents matching the query.

        :param _limit: Maximum number of documents to return
        :param kwargs: Fields to match in the documents
        :return: List of documents matching the query
        """

    @abstractmethod
    def find_one(_self, **kwargs: Any):
        """
        Find a single document matching the query.

        If multiple documents match the query, an arbitrary matching
        document is returned.

        :param kwargs: Fields to match in the document
        :return: Document matching the query, or None if not found
        """

    @abstractmethod
    def update(_self, _data: dict | TModel, /, **kwargs: Any):
        """
        Update documents matching the query.

        Note that the data must be a full object, not just the fields to update.

        :param _data: Data to update with (must be a full object)
        :param kwargs: Fields to match in the documents
        :return: Number of documents updated
        """

    @abstractmethod
    def delete(_self, /, **kwargs: Any):
        """
        Delete documents matching the query.

        :param kwargs: Fields to match in the documents
        :return: Number of documents deleted
        """

    @abstractmethod
    def set(_self, _fields: dict[str, Any], **kwargs: Any):
        """
        Update specific fields in documents matching the query.

        :param _fields: Fields to update
        :param kwargs: Fields to match in the documents
        :return: Number of documents updated
        """

    @abstractmethod
    def clear(self):
        """
        Delete all documents in the collection.

        :return: Number of documents deleted
        """
