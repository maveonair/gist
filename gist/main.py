from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse

from . import crud, forms, models
from .database import SessionLocal, engine

templates = Jinja2Templates(
    directory="templates",
    extensions=[
        "jinja2_humanize_extension.HumanizeExtension",
    ],
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
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
def get_root(request: Request, db: Session = Depends(get_db)):
    recent_entries = crud.get_recent_entries(db)
    return templates.TemplateResponse(
        "index.html", {"request": request, "entries": recent_entries}
    )


@app.get("/entries")
def get_entries(
    request: Request,
    query: str = "",
    skip: int = 0,
    db: Session = Depends(get_db),
):
    default_limit = 5

    entries = crud.get_entries(db, query=query, skip=skip, limit=default_limit)
    has_more_entries = crud.count_entries(db, query=query) > skip + default_limit

    context = {
        "request": request,
        "entries": entries,
        "query": query,
        "skip": skip,
        "limit": default_limit,
        "has_more_entries": has_more_entries,
    }

    if "HX-Request" in request.headers:
        return templates.TemplateResponse("entries/_entries.html", context=context)

    return templates.TemplateResponse("entries/index.html", context=context)


@app.get("/entries/autocomplete")
def search_entries(
    request: Request,
    query: str,
    db: Session = Depends(get_db),
):
    if "HX-Request" in request.headers:
        hasQuery = True if len(query) > 0 else False
        entries = crud.get_entries(db, query=query, limit=5)
        return templates.TemplateResponse(
            "entries/search_results.html",
            {
                "request": request,
                "hasQuery": hasQuery,
                "entries": entries,
            },
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


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
            {"request": request, "entries": recent_entries, "form": form},
        )


@app.get("/{entry_id}")
def get_entry(request: Request, entry_id: int, db: Session = Depends(get_db)):
    entry = crud.get_entry(db, entry_id=entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return templates.TemplateResponse(
        "entries/show.html", {"request": request, "entry": entry}
    )


@app.get("/{entry_id}/edit")
def edit_entry(request: Request, entry_id: int, db: Session = Depends(get_db)):
    # TODO: Maybe we don't need this check?
    entry = crud.get_entry(db, entry_id=entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    form = forms.EntryEditForm(request=request, db=db, entry_id=entry_id)
    return templates.TemplateResponse(
        "entries/edit.html", {"request": request, "form": form}
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
            "entries/edit.html",
            {"request": request, "form": form},
        )


@app.delete("/{entry_id}")
def delete_entry(
    request: Request,
    entry_id: int,
    db: Session = Depends(get_db),
):
    entry = crud.get_entry(db, entry_id=entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    crud.delete_entry(db, entry=entry)

    response = templates.TemplateResponse("index.html", {"request": request})
    response.headers["hx-redirect"] = "/"
    return response
