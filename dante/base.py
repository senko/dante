from __future__ import annotations

import json
from datetime import date, datetime

from pydantic import BaseModel


class DanteEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime) or isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


class BaseDante:
    MEMORY = ":memory:"

    def __init__(self, db_name: str = MEMORY, auto_commit: bool = True):
        self.db_name = db_name
        self.conn = None
        self.auto_commit = auto_commit

    def __str__(self):
        return f'<{self.__class__.__name__}("{self.db_name}")>'

    def get_connection(self):
        raise NotImplementedError()

    def collection(self, name: str, model: BaseModel | None = None) -> "BaseCollection":
        raise NotImplementedError()

    def __getitem__(self, name: str | type) -> "BaseCollection":
        if isinstance(name, type) and issubclass(name, BaseModel):
            return self.collection(name.__name__, name)
        else:
            return self.collection(name)


class BaseCollection:
    def __init__(self, name: str, db: BaseDante, model: BaseModel | None = None):
        self.name = name
        self.db = db
        self.conn = db.conn
        self.model = model

    def __str__(self):
        return f'<{self.__class__.__name__}("{self.db.db_name}/{self.name}")>'

    def _to_json(self, data: dict | BaseModel) -> str:
        if self.model and isinstance(data, BaseModel):
            return data.model_dump_json()
        else:
            return json.dumps(data, cls=DanteEncoder)

    def _from_json(self, json_text: str) -> dict | BaseModel:
        data = json.loads(json_text)
        return self.model(**data) if self.model else data

    def _build_query(_self, _limit, /, **kwargs) -> tuple[str, list]:
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
