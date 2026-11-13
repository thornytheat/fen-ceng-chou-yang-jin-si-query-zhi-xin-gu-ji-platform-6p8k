"""近似查询 controller。"""
from __future__ import annotations

from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.services import export_service, qc_service, query_service


def list_queries(db: Session, plan_id: int | None = None, limit: int = 40) -> dict:
    rows = query_service.list_queries(db, plan_id, limit)
    items = [query_service.query_out(db, row) for row in rows]
    return {"items": items, "total": len(items)}


def get_query(db: Session, query_id: int) -> dict:
    return query_service.query_out(db, query_service.get_query(db, query_id))


def run_query(db: Session, payload, actor: dict, ip: str | None = None) -> dict:
    row = query_service.run_query(db, payload.plan_id, payload.strata, payload.note, actor, ip)
    db.commit()
    return query_service.query_out(db, query_service.get_query(db, row.id))


def export_query(db: Session, query_id: int) -> Response:
    row = query_service.get_query(db, query_id)
    from sqlalchemy import select

    from src.models.qc_check import QcCheck

    qc = db.scalar(select(QcCheck).where(QcCheck.query_id == row.id))
    filename, content = export_service.build_estimate_markdown(row, qc)
    return Response(
        content=content.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
