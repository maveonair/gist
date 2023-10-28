from datetime import datetime, UTC

from sqlalchemy.orm import Session

from . import models, schemas


def entry_exists(db: Session, description: str, entry_id: int = None) -> bool:
    entry = (
        db.query(models.Entry).filter(models.Entry.description == description).first()
    )

    return entry is not None and entry.id != entry_id


def get_recent_entries(db: Session) -> [models.Entry]:
    return db.query(models.Entry).order_by(models.Entry.updated_at.desc()).limit(5)


def get_entries(
    db: Session, query: str = None, skip: int = 0, limit: int = 100
) -> [models.Entry]:
    if query is None:
        return (
            db.query(models.Entry)
            .order_by(models.Entry.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    return (
        db.query(models.Entry)
        .filter(
            models.Entry.description.ilike(f"%{query}%")
            | models.Entry.content.ilike(f"%{query}%")
        )
        .order_by(models.Entry.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_entry(db: Session, entry_id: int) -> models.Entry:
    return db.query(models.Entry).filter(models.Entry.id == entry_id).first()


def create_entry(db: Session, entry: schemas.EntryCreate) -> models.Entry:
    db_entry = models.Entry(
        description=entry.description,
        content=entry.content,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


def edit_entry(db: Session, entry: schemas.Entry) -> models.Entry:
    db_entry = db.query(models.Entry).filter(models.Entry.id == entry.id).first()
    db_entry.description = entry.description
    db_entry.content = entry.content
    db_entry.updated_at = datetime.now(UTC).astimezone()
    db.commit()
    db.refresh(db_entry)
    return db_entry


def delete_entry(db: Session, entry: schemas.Entry):
    db_entry = db.query(models.Entry).filter(models.Entry.id == entry.id).first()
    db.delete(db_entry)
    db.commit()
