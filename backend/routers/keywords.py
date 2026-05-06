import csv
import io
import logging
import re
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import desc

from database import get_db
from models.keyword import Keyword, KeywordList, KeywordListItem
from models.research import KeywordResearchRun
from routers._helpers import get_project_or_404, to_csv
from schemas.common import ok
from schemas.keyword import (
    BulkTrackRequest,
    KeywordImportRequest,
    KeywordListCreate,
    KeywordListOut,
    KeywordOut,
    ResearchHistoryDetail,
    ResearchHistoryOut,
    ResearchKeyword,
    ResearchRequest,
    ResearchResult,
    SaveKeywordsRequest,
)
from services import dataforseo, suggest

router = APIRouter(prefix="/api/projects/{project_id}", tags=["keywords"])
log = logging.getLogger(__name__)


@router.post("/keywords/research")
async def research(
    project_id: uuid.UUID, payload: ResearchRequest, db: AsyncSession = Depends(get_db)
):
    """Recursive Google Suggest expansion + DataForSEO metrics enrichment."""
    await get_project_or_404(db, project_id)

    expanded = await suggest.expand(
        seed=payload.seed,
        country=payload.country,
        levels=payload.suggest_levels,
        max_results=payload.max_results,
    )
    # Always include the seed itself.
    if payload.seed.lower() not in expanded:
        expanded = [payload.seed.lower(), *expanded]

    metrics_by_kw: dict = {}
    if payload.include_metrics and expanded:
        try:
            # DataForSEO accepts up to 1000 keywords per call.
            for i in range(0, len(expanded), 700):
                chunk = expanded[i:i + 700]
                items = await dataforseo.keyword_overview(chunk, country=payload.country)
                for it in items:
                    kw = (it.get("keyword") or "").lower()
                    if not kw:
                        continue
                    info = it.get("keyword_info") or {}
                    props = it.get("keyword_properties") or {}
                    intent = (it.get("search_intent_info") or {}).get("main_intent")
                    metrics_by_kw[kw] = {
                        "search_volume": info.get("search_volume"),
                        "cpc": info.get("cpc"),
                        "competition": info.get("competition_level"),
                        "keyword_difficulty": props.get("keyword_difficulty"),
                        "intent": intent,
                        "monthly_searches": info.get("monthly_searches") or [],
                    }
        except Exception as e:
            log.warning("DataForSEO enrichment failed: %s", e)

    rows = []
    for kw in expanded:
        m = metrics_by_kw.get(kw, {})
        rows.append(ResearchKeyword(
            keyword=kw,
            search_volume=m.get("search_volume"),
            keyword_difficulty=m.get("keyword_difficulty"),
            cpc=m.get("cpc"),
            competition=m.get("competition"),
            intent=m.get("intent"),
            monthly_searches=m.get("monthly_searches") or [],
        ))
    rows.sort(key=lambda r: (r.search_volume or 0), reverse=True)
    result = ResearchResult(seed=payload.seed, country=payload.country, total=len(rows), keywords=rows)

    # Auto-save: every research run is persisted so the user can reload it later.
    run = KeywordResearchRun(
        project_id=project_id,
        seed=payload.seed.strip().lower(),
        country=payload.country.upper(),
        suggest_levels=payload.suggest_levels,
        total=len(rows),
        keywords=[r.model_dump(mode="json") for r in rows],
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    return ok({**result.model_dump(mode="json"), "run_id": str(run.id)})


# ---------- Research history ----------

@router.get("/keywords/research/history")
async def research_history(
    project_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    await get_project_or_404(db, project_id)
    rows = (await db.execute(
        select(KeywordResearchRun)
        .where(KeywordResearchRun.project_id == project_id)
        .order_by(desc(KeywordResearchRun.created_at)).limit(limit)
    )).scalars().all()
    return ok([ResearchHistoryOut.model_validate(r).model_dump(mode="json") for r in rows])


@router.get("/keywords/research/history/{run_id}")
async def research_history_one(
    project_id: uuid.UUID, run_id: uuid.UUID, db: AsyncSession = Depends(get_db),
):
    rec = await db.get(KeywordResearchRun, run_id)
    if not rec or rec.project_id != project_id:
        raise HTTPException(404, "Research run not found")
    return ok(ResearchHistoryDetail.model_validate(rec).model_dump(mode="json"))


@router.delete("/keywords/research/history/{run_id}")
async def research_history_delete(
    project_id: uuid.UUID, run_id: uuid.UUID, db: AsyncSession = Depends(get_db),
):
    rec = await db.get(KeywordResearchRun, run_id)
    if not rec or rec.project_id != project_id:
        raise HTTPException(404, "Research run not found")
    await db.delete(rec)
    await db.commit()
    return ok({"deleted": str(run_id)})


@router.get("/keywords/related")
async def related(
    project_id: uuid.UUID,
    keyword: str = Query(min_length=1),
    country: str = Query(default="US"),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    await get_project_or_404(db, project_id)
    items = await dataforseo.related_keywords(keyword, country=country.upper(), limit=limit)
    return ok({"seed": keyword, "country": country.upper(), "items": items})


@router.get("/keywords/questions")
async def questions(
    project_id: uuid.UUID,
    keyword: str = Query(min_length=1),
    country: str = Query(default="US"),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    await get_project_or_404(db, project_id)
    items = await dataforseo.keyword_questions(keyword, country=country.upper(), limit=limit)
    return ok({"seed": keyword, "country": country.upper(), "items": items})


@router.get("/keywords")
async def list_keywords(
    project_id: uuid.UUID,
    tracked: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    await get_project_or_404(db, project_id)
    stmt = select(Keyword).where(Keyword.project_id == project_id)
    if tracked is not None:
        stmt = stmt.where(Keyword.tracked.is_(tracked))
    if search:
        stmt = stmt.where(Keyword.keyword.ilike(f"%{search.lower()}%"))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Keyword.created_at.desc()).limit(page_size).offset((page - 1) * page_size)
    rows = (await db.execute(stmt)).scalars().all()
    return ok({
        "items": [KeywordOut.model_validate(r).model_dump(mode="json") for r in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
    })


@router.post("/keywords/save", status_code=status.HTTP_201_CREATED)
async def save_keywords(
    project_id: uuid.UUID, payload: SaveKeywordsRequest, db: AsyncSession = Depends(get_db)
):
    await get_project_or_404(db, project_id)
    saved: List[Keyword] = []
    skipped: int = 0
    country = payload.country.upper()

    for kw in payload.keywords:
        existing = await db.execute(
            select(Keyword).where(
                Keyword.project_id == project_id,
                Keyword.keyword == kw.keyword.lower(),
                Keyword.country == country,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            # Update metrics if provided
            row.search_volume = kw.search_volume if kw.search_volume is not None else row.search_volume
            row.keyword_difficulty = kw.keyword_difficulty if kw.keyword_difficulty is not None else row.keyword_difficulty
            row.cpc = kw.cpc if kw.cpc is not None else row.cpc
            row.intent = kw.intent or row.intent
            if payload.track:
                row.tracked = True
            skipped += 1
            continue
        saved.append(Keyword(
            project_id=project_id,
            keyword=kw.keyword.lower(),
            country=country,
            search_volume=kw.search_volume,
            keyword_difficulty=kw.keyword_difficulty,
            cpc=kw.cpc,
            intent=kw.intent,
            tracked=payload.track,
        ))
    db.add_all(saved)
    await db.commit()
    return ok({"saved": len(saved), "updated_or_skipped": skipped})


@router.delete("/keywords/{keyword_id}")
async def delete_keyword(
    project_id: uuid.UUID, keyword_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    kw = await db.get(Keyword, keyword_id)
    if not kw or kw.project_id != project_id:
        raise HTTPException(404, "Keyword not found")
    await db.delete(kw)
    await db.commit()
    return ok({"deleted": str(keyword_id)})


@router.post("/keywords/bulk-track")
async def bulk_track(
    project_id: uuid.UUID, payload: BulkTrackRequest, db: AsyncSession = Depends(get_db)
):
    """Set tracked=True/False on many keywords at once."""
    await get_project_or_404(db, project_id)
    if not payload.keyword_ids:
        return ok({"updated": 0})
    rows = (await db.execute(
        select(Keyword).where(
            Keyword.project_id == project_id,
            Keyword.id.in_(payload.keyword_ids),
        )
    )).scalars().all()
    for kw in rows:
        kw.tracked = payload.tracked
    await db.commit()
    return ok({"updated": len(rows), "tracked": payload.tracked})


_NUMERIC_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _to_int(v) -> Optional[int]:
    if v is None or v == "":
        return None
    m = _NUMERIC_RE.search(str(v))
    return int(float(m.group())) if m else None


def _to_float(v) -> Optional[float]:
    if v is None or v == "":
        return None
    m = _NUMERIC_RE.search(str(v).replace(",", "."))
    return float(m.group()) if m else None


def _parse_import_text(text: str, default_country: str, track: bool) -> List[dict]:
    text = (text or "").strip()
    if not text:
        return []

    first_line = text.split("\n", 1)[0].lower()
    is_csv = ("," in first_line or ";" in first_line) and any(
        h in first_line for h in ("keyword", "kw", "query", "term")
    )

    rows: List[dict] = []
    if is_csv:
        # Detect delimiter
        delim = ";" if first_line.count(";") > first_line.count(",") else ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delim)
        for raw in reader:
            normalised = {k.strip().lower(): (v.strip() if isinstance(v, str) else v)
                          for k, v in (raw or {}).items() if k}
            kw = normalised.get("keyword") or normalised.get("kw") or normalised.get("query") or normalised.get("term")
            if not kw:
                continue
            country = (normalised.get("country") or normalised.get("geo") or default_country)[:2].upper()
            rows.append({
                "keyword": kw.lower(),
                "country": country,
                "search_volume": _to_int(normalised.get("search_volume") or normalised.get("volume")),
                "keyword_difficulty": _to_float(normalised.get("keyword_difficulty") or normalised.get("kd")),
                "cpc": _to_float(normalised.get("cpc")),
                "intent": normalised.get("intent"),
                "tracked": track or normalised.get("tracked", "").lower() in ("true", "1", "yes"),
            })
    else:
        # one keyword per line
        for line in text.splitlines():
            kw = line.strip().lstrip("-•").strip()
            if not kw:
                continue
            rows.append({
                "keyword": kw.lower(),
                "country": default_country.upper(),
                "search_volume": None,
                "keyword_difficulty": None,
                "cpc": None,
                "intent": None,
                "tracked": track,
            })
    return rows


@router.post("/keywords/import")
async def import_keywords(
    project_id: uuid.UUID, payload: KeywordImportRequest, db: AsyncSession = Depends(get_db)
):
    """Bulk import: paste a CSV (with header `keyword,...`) or a plain list,
    one keyword per line. Auto-detects format. Existing rows for the same
    (project, keyword, country) are updated, new ones are created."""
    await get_project_or_404(db, project_id)
    rows = _parse_import_text(payload.text, payload.country, payload.track)
    if not rows:
        raise HTTPException(400, "No valid keywords found in input")

    saved = 0
    updated = 0
    for r in rows:
        existing = (await db.execute(
            select(Keyword).where(
                Keyword.project_id == project_id,
                Keyword.keyword == r["keyword"],
                Keyword.country == r["country"],
            )
        )).scalar_one_or_none()
        if existing:
            for f in ("search_volume", "keyword_difficulty", "cpc", "intent"):
                if r.get(f) is not None:
                    setattr(existing, f, r[f])
            if r.get("tracked"):
                existing.tracked = True
            updated += 1
        else:
            db.add(Keyword(
                project_id=project_id,
                keyword=r["keyword"],
                country=r["country"],
                search_volume=r.get("search_volume"),
                keyword_difficulty=r.get("keyword_difficulty"),
                cpc=r.get("cpc"),
                intent=r.get("intent"),
                tracked=bool(r.get("tracked")),
            ))
            saved += 1
    await db.commit()
    return ok({"saved": saved, "updated": updated, "total": len(rows)})


@router.post("/keywords/bulk-delete")
async def bulk_delete(
    project_id: uuid.UUID, payload: BulkTrackRequest, db: AsyncSession = Depends(get_db)
):
    """Delete many keywords at once. Reuses BulkTrackRequest body shape."""
    await get_project_or_404(db, project_id)
    if not payload.keyword_ids:
        return ok({"deleted": 0})
    rows = (await db.execute(
        select(Keyword).where(
            Keyword.project_id == project_id,
            Keyword.id.in_(payload.keyword_ids),
        )
    )).scalars().all()
    for kw in rows:
        await db.delete(kw)
    await db.commit()
    return ok({"deleted": len(rows)})


@router.get("/keywords/export.csv")
async def export_csv(
    project_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    await get_project_or_404(db, project_id)
    rows = (await db.execute(
        select(Keyword).where(Keyword.project_id == project_id).order_by(Keyword.created_at.desc())
    )).scalars().all()
    csv_text = to_csv(
        [{
            "keyword": r.keyword, "country": r.country,
            "search_volume": r.search_volume, "keyword_difficulty": r.keyword_difficulty,
            "cpc": r.cpc, "intent": r.intent, "tracked": r.tracked,
        } for r in rows],
        ["keyword", "country", "search_volume", "keyword_difficulty", "cpc", "intent", "tracked"],
    )
    return Response(content=csv_text, media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="keywords-{project_id}.csv"'})


# ---------- Keyword Lists ----------

@router.get("/keyword-lists")
async def list_lists(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await get_project_or_404(db, project_id)
    rows = (await db.execute(
        select(KeywordList).where(KeywordList.project_id == project_id).order_by(KeywordList.created_at.desc())
    )).scalars().all()
    out = []
    for lst in rows:
        cnt = (await db.execute(
            select(func.count()).select_from(KeywordListItem).where(KeywordListItem.list_id == lst.id)
        )).scalar_one()
        out.append({**KeywordListOut.model_validate(lst).model_dump(mode="json"), "keyword_count": cnt})
    return ok(out)


@router.post("/keyword-lists", status_code=status.HTTP_201_CREATED)
async def create_list(
    project_id: uuid.UUID, payload: KeywordListCreate, db: AsyncSession = Depends(get_db)
):
    await get_project_or_404(db, project_id)
    lst = KeywordList(project_id=project_id, name=payload.name)
    db.add(lst)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "A list with this name already exists")
    for kid in payload.keyword_ids:
        db.add(KeywordListItem(list_id=lst.id, keyword_id=kid))
    await db.commit()
    await db.refresh(lst)
    return ok(KeywordListOut.model_validate(lst).model_dump(mode="json"))


@router.get("/keyword-lists/{list_id}")
async def get_list(project_id: uuid.UUID, list_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    lst = await db.get(KeywordList, list_id)
    if not lst or lst.project_id != project_id:
        raise HTTPException(404, "List not found")
    rows = (await db.execute(
        select(Keyword).join(KeywordListItem, KeywordListItem.keyword_id == Keyword.id)
        .where(KeywordListItem.list_id == list_id)
    )).scalars().all()
    return ok({
        "list": KeywordListOut.model_validate(lst).model_dump(mode="json"),
        "items": [KeywordOut.model_validate(r).model_dump(mode="json") for r in rows],
    })


@router.delete("/keyword-lists/{list_id}")
async def delete_list(project_id: uuid.UUID, list_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    lst = await db.get(KeywordList, list_id)
    if not lst or lst.project_id != project_id:
        raise HTTPException(404, "List not found")
    await db.delete(lst)
    await db.commit()
    return ok({"deleted": str(list_id)})
