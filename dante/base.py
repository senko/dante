from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


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
    """

    MEMORY = ":memory:"

    def __init__(self, db_name: str = MEMORY, auto_commit: bool = True):
        """
        Initialize the Dante instance.

        :param db_name: Name of the database, defaults to in-memory database
        :param auto_commit: Whether to automatically commit transactions, defaults to True
        """
        self.db_name = db_name
        self.conn = None
        self.auto_commit = auto_commit

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
    def collection(self, name: str, model: type | None = None) -> "BaseCollection":
        """
        Get a collection from the database.

        :param name: Name of the collection
        :param model: Pydantic model class (if using with Pydantic)

        :return: Collection instance
        """

    def __getitem__(self, name: str | type) -> "BaseCollection":
        """
        Get a collection using dictionary-like syntax.

        :param name: Name of the collection or a Pydantic model class
        :return: Collection instance
        """
        if isinstance(name, type) and issubclass(name, BaseModel):
            return self.collection(name.__name__, name)
        else:
            return self.collection(name)

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

    def __init__(self, name: str, db: BaseDante, model: BaseModel | None = None):
        """
        Initialize the BaseCollection instance.

        :param name: Name of the collection
        :param db: BaseDante instance representing the database
        :param model: Optional Pydantic model class for data validation and serialization
        """
        self.name = name
        self.db = db
        self.conn = db.conn
        self.model = model

    def __str__(self) -> str:
        """
        Return a string representation of the BaseCollection instance.

        :return: String representation of the instance
        """
        return f'<{self.__class__.__name__}("{self.db.db_name}/{self.name}")>'

    def _to_json(self, data: dict | BaseModel) -> str:
        """
        Internal method to serialize data to JSON before saving.

        :param data: Data or Pydantic object to serialize
        :return: JSON-serialized data
        """
        if self.model and isinstance(data, BaseModel):
            return data.model_dump_json()
        else:
            return json.dumps(data, cls=DanteEncoder)

    def _from_json(self, json_text: str) -> dict | BaseModel:
        """
        Internal method to parse JSON data after loading.

        :param json_text: Raw JSON data to parse
        :return: Deserialized data as dictionary or Pydantic model
        """
        data = json.loads(json_text)
        return self.model(**data) if self.model else data

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
                query_parts.append("data->>? = ?")
                values.extend([key, value])
            query = " WHERE " + " AND ".join(query_parts)
        else:
            query = ""

        if _limit:
            query += f" LIMIT {_limit}"

        return query, values

    @abstractmethod
    def insert(self, data: dict | BaseModel):
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
    ) -> list[dict | BaseModel]:
        """
        Find documents matching the query.

        :param _limit: Maximum number of documents to return
        :param kwargs: Fields to match in the documents
        :return: List of documents matching the query
        """

    @abstractmethod
    def find_one(_self, **kwargs: Any) -> dict | BaseModel | None:
        """
        Find a single document matching the query.

        If multiple documents match the query, an arbitrary matching
        document is returned.

        :param kwargs: Fields to match in the document
        :return: Document matching the query, or None if not found
        """

    @abstractmethod
    def update_many(
        _self,
        _data: dict | BaseModel,
        _limit: int | None = None,
        /,
        **kwargs: Any,
    ):
        """
        Update documents matching the query.

        Note that the data must be a full object, not just the fields to update.

        :param _data: Data to update with (must be a full object)
        :param _limit: Maximum number of documents to update (default is no limit)
        :param kwargs: Fields to match in the documents
        """

    @abstractmethod
    def update_one(_self, _data: dict | BaseModel, /, **kwargs: Any):
        """
        Update one document matching the query.

        Note that the data must be a full object, not just the fields to update.

        :param _data: Data to update with (must be a full object)
        :param kwargs: Fields to match in the document
        """

    @abstractmethod
    def delete_many(_self, _limit: int | None = None, /, **kwargs: Any):
        """
        Delete documents matching the query.

        :param _limit: Maximum number of documents to delete (default is no limit)
        :param kwargs: Fields to match in the documents
        """

    @abstractmethod
    def delete_one(_self, /, **kwargs: Any):
        """
        Delete one document matching the query.

        :param kwargs: Fields to match in the document
        """

    @abstractmethod
    def clear(self):
        """
        Delete all documents in the collection.
        """
