from fastapi import APIRouter, Query

from app.core.response import success
from app.services.catalog import build_filters, get_search_suggestions

router = APIRouter(prefix="/api/v1", tags=["meta"])


@router.get("/meta/filters")
def meta_filters():
    return success(build_filters())


@router.get("/search/suggest")
def search_suggest(q: str = Query(default="", min_length=1)):
    return success(get_search_suggestions(q))
