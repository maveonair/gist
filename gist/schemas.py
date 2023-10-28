from datetime import datetime, UTC

from pydantic import BaseModel


class EntryBase(BaseModel):
    description: str
    content: str
    created_at: datetime = datetime.now(UTC).astimezone()
    updated_at: datetime = datetime.now(UTC).astimezone()


class EntryCreate(EntryBase):
    pass


class Entry(EntryBase):
    id: int

    class Config:
        from_attributes = True
