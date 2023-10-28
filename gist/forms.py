from datetime import datetime
from typing import Dict

from sqlalchemy.orm import Session
from starlette.requests import Request

from gist import crud, schemas


class EntryForm:
    db: Session = None
    entry_id: int = None
    description: str = None
    content: str = None
    errors: Dict[str, str] = {}

    async def submit(self):
        raise NotImplementedError

    def _is_valid(self):
        self.errors.clear()

        # TODO: unique only if not same entry
        if not self.description:
            self.errors["description"] = "Description is required"

        if not self.content:
            self.errors["content"] = "Content is required"

        if crud.entry_exists(
            db=self.db, description=self.description, entry_id=self.entry_id
        ):
            self.errors["description"] = "Description must be unique"

        return len(self.errors) == 0


class EntryCreateForm(EntryForm):
    def __init__(self, request: Request, db: Session):
        self.request = request
        self.db = db
        self.errors: Dict[str, str] = {}

    async def submit(self) -> bool:
        form = await self.request.form()
        self.description = form.get("description")
        self.content = form.get("content")

        if not self._is_valid():
            return False

        try:
            entry = schemas.EntryCreate(
                description=self.description, content=self.content
            )
            entity = crud.create_entry(db=self.db, entry=entry)
            self.entry_id = entity.id
        except Exception as e:
            self.errors["error"] = str(e)
            return False

        return True


class EntryEditForm(EntryForm):
    created_at: datetime = None

    def __init__(
        self,
        request: Request,
        db: Session,
        entry_id: int,
    ):
        self.entry_id = entry_id
        self.request = request
        self.db = db

        entry = crud.get_entry(db, entry_id)
        self.description = entry.description
        self.content = entry.content
        self.created_at = entry.created_at

    async def submit(self) -> bool:
        form = await self.request.form()
        self.description = form.get("description")
        self.content = form.get("content")

        if not self._is_valid():
            return False

        try:
            entry = schemas.Entry(
                id=self.entry_id, description=self.description, content=self.content
            )
            crud.edit_entry(self.db, entry=entry)
        except Exception as e:
            self.errors["error"] = str(e)
            return False

        return True
