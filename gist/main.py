from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse

from . import crud, models, forms
from .database import SessionLocal, engine

templates = Jinja2Templates(
    directory="templates",
    extensions=[
        "jinja2_humanize_extension.HumanizeExtension",
    ],
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.exception_handler(404)
async def custom_404_handler(request, __):
    return templates.TemplateResponse("404.html", {"request": request})


@app.get("/")
def get_entries(request: Request, db: Session = Depends(get_db)):
    recent_entries = crud.get_recent_entries(db)
    return templates.TemplateResponse(
        "index.html", {"request": request, "entries": recent_entries.all()}
    )


@app.get("/entries")
def get_entries(
    request: Request,
    q: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    entries = crud.get_entries(db, query=q, skip=skip, limit=limit)
    return templates.TemplateResponse(
        "entries.html", {"request": request, "entries": entries}
    )


@app.post("/entries")
async def create_entry(
    request: Request,
    db: Session = Depends(get_db),
):
    form = forms.EntryCreateForm(request=request, db=db)
    if await form.submit():
        return RedirectResponse(
            url=f"/{form.entry_id}", status_code=status.HTTP_302_FOUND
        )
    else:
        recent_entries = crud.get_recent_entries(db)
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "entries": recent_entries.all(), "form": form},
        )


@app.get("/{entry_id}")
def get_entry(request: Request, entry_id: int, db: Session = Depends(get_db)):
    entry = crud.get_entry(db, entry_id=entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return templates.TemplateResponse(
        "entry.html", {"request": request, "entry": entry}
    )


@app.get("/{entry_id}/edit")
def edit_entry(request: Request, entry_id: int, db: Session = Depends(get_db)):
    # TODO: Maybe we don't need this check?
    entry = crud.get_entry(db, entry_id=entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    form = forms.EntryEditForm(request=request, db=db, entry_id=entry_id)
    return templates.TemplateResponse(
        "edit_entry.html", {"request": request, "form": form}
    )


@app.post("/{entry_id}/update")
async def update_entry(
    request: Request,
    entry_id: int,
    db: Session = Depends(get_db),
):
    form = forms.EntryEditForm(request=request, db=db, entry_id=entry_id)
    if await form.submit():
        return RedirectResponse(
            url=f"/{form.entry_id}", status_code=status.HTTP_302_FOUND
        )
    else:
        return templates.TemplateResponse(
            "edit_entry.html",
            {"request": request, "form": form},
        )


@app.get("/{entry_id}/delete")
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = crud.get_entry(db, entry_id=entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    crud.delete_entry(db, entry=entry)
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
