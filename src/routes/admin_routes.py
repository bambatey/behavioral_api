from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.datalayer.database import get_db
from src.datalayer.model import BIAS_OBJECT, BIAS_SUBJECT, Context, Filler, Sentence
from src.datalayer.repository import (
    ContextRepository,
    FillerRepository,
    SentenceRepository,
)
from src.middleware import verify_jwt_token
from src.services import ExportService, ResultsService

if TYPE_CHECKING:
    from firebase_admin.firestore_async import AsyncClient


router = APIRouter(prefix="/admin", tags=["Admin"])


# ---------- Participant overview ----------

class ParticipantInfo(BaseModel):
    id: str
    name: str
    assignment_index: int
    session_id: str
    created_at: str
    trial_count: int


class TrialInfo(BaseModel):
    id: str
    trial_index: int
    is_filler: bool
    context_id: Optional[str] = None
    context_text: Optional[str] = None
    sentence_id: Optional[str] = None
    sentence_text: Optional[str] = None
    bias: Optional[str] = None
    position: Optional[int] = None
    response: Optional[int] = None  # 1..7 Likert
    correct_answer: Optional[bool] = None
    rt: Optional[float] = None


class ParticipantDetailsResponse(BaseModel):
    participant: ParticipantInfo
    trials: List[TrialInfo]


@router.get("/participants", response_model=List[ParticipantInfo])
async def list_participants(
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    service = ResultsService(db)
    participants = await service.get_all_participants()
    result: List[ParticipantInfo] = []
    for p in participants:
        trial_count = await service.trial_repo.count_by_participant(p.id)
        result.append(
            ParticipantInfo(
                id=p.id,
                name=p.name,
                assignment_index=p.assignment_index,
                session_id=p.session_id,
                created_at=p.created_at.isoformat(),
                trial_count=trial_count,
            )
        )
    result.sort(key=lambda x: x.created_at, reverse=True)
    return result


@router.get("/participants/{participant_id}", response_model=ParticipantDetailsResponse)
async def get_participant_results(
    participant_id: str,
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    service = ResultsService(db)
    result = await service.get_participant_results(participant_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")
    p = result["participant"]
    trials = result["trials"]
    return ParticipantDetailsResponse(
        participant=ParticipantInfo(
            id=p.id,
            name=p.name,
            assignment_index=p.assignment_index,
            session_id=p.session_id,
            created_at=p.created_at.isoformat(),
            trial_count=len(trials),
        ),
        trials=[
            TrialInfo(
                id=t.id,
                trial_index=t.trial_index,
                is_filler=t.is_filler,
                context_id=t.context_id,
                context_text=t.context_text,
                sentence_id=t.sentence_id,
                sentence_text=t.sentence_text,
                bias=t.bias,
                position=t.position,
                response=t.response,
                correct_answer=t.correct_answer,
                rt=t.rt,
            )
            for t in trials
        ],
    )


@router.get("/export")
async def export_all_results(
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    service = ExportService(db)
    excel_bytes = await service.export_to_excel()
    return StreamingResponse(
        iter([excel_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=all_results.xlsx"},
    )


@router.get("/export/{participant_id}")
async def export_participant_results(
    participant_id: str,
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    service = ExportService(db)
    participant = await service.participant_repo.get_by_id(participant_id)
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")
    excel_bytes = await service.export_to_excel(participant_id)
    filename = f"{participant.name}_results.xlsx".replace(" ", "_")
    return StreamingResponse(
        iter([excel_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/stats")
async def get_statistics(
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    service = ResultsService(db)
    all_trials = await service.trial_repo.get_all()
    participants = await service.get_all_participants()

    if not all_trials:
        return {
            "total_participants": len(participants),
            "total_trials": 0,
            "critical_count": 0,
            "filler_count": 0,
            "avg_rt": None,
            "avg_likert": None,
        }

    critical = [t for t in all_trials if not t.is_filler]
    fillers = [t for t in all_trials if t.is_filler]
    rts = [t.rt for t in critical if t.rt is not None]
    likerts = [t.response for t in critical if isinstance(t.response, int)]
    return {
        "total_participants": len(participants),
        "total_trials": len(all_trials),
        "critical_count": len(critical),
        "filler_count": len(fillers),
        "avg_rt": round(sum(rts) / len(rts), 2) if rts else None,
        "avg_likert": round(sum(likerts) / len(likerts), 2) if likerts else None,
    }


# ---------- Context CRUD ----------

class ContextPayload(BaseModel):
    title: str
    text: str
    bias: str  # "subject" | "object"
    order_index: int
    is_active: Optional[bool] = True


class ContextResponse(BaseModel):
    id: str
    title: str
    text: str
    bias: str
    order_index: int
    is_active: bool
    created_at: str
    updated_at: str


def _context_to_response(c: Context) -> ContextResponse:
    return ContextResponse(
        id=c.id,
        title=c.title,
        text=c.text,
        bias=c.bias,
        order_index=c.order_index,
        is_active=c.is_active,
        created_at=c.created_at.isoformat(),
        updated_at=c.updated_at.isoformat(),
    )


def _validate_context_payload(payload: ContextPayload) -> None:
    if payload.bias not in (BIAS_SUBJECT, BIAS_OBJECT):
        raise HTTPException(status_code=400, detail="bias must be 'subject' or 'object'")


@router.get("/contexts", response_model=List[ContextResponse])
async def list_contexts(
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    repo = ContextRepository(db)
    return [_context_to_response(c) for c in await repo.list_all_ordered()]


@router.post("/contexts", response_model=ContextResponse, status_code=201)
async def create_context(
    payload: ContextPayload,
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    _validate_context_payload(payload)
    repo = ContextRepository(db)
    ctx = Context.create(
        title=payload.title,
        text=payload.text,
        bias=payload.bias,
        order_index=payload.order_index,
    )
    if payload.is_active is not None:
        ctx.is_active = payload.is_active
    await repo.save(ctx)
    return _context_to_response(ctx)


@router.put("/contexts/{context_id}", response_model=ContextResponse)
async def update_context(
    context_id: str,
    payload: ContextPayload,
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    _validate_context_payload(payload)
    repo = ContextRepository(db)
    ctx = await repo.get_by_id(context_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Context not found")
    ctx.title = payload.title
    ctx.text = payload.text
    ctx.bias = payload.bias
    ctx.order_index = payload.order_index
    if payload.is_active is not None:
        ctx.is_active = payload.is_active
    ctx.updated_at = datetime.utcnow()
    await repo.save(ctx)
    return _context_to_response(ctx)


@router.delete("/contexts/{context_id}", status_code=204)
async def delete_context(
    context_id: str,
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    ctx_repo = ContextRepository(db)
    if not await ctx_repo.exists(context_id):
        raise HTTPException(status_code=404, detail="Context not found")
    sent_repo = SentenceRepository(db)
    await sent_repo.delete_by_context(context_id)
    await ctx_repo.delete_by_id(context_id)


# ---------- Sentence CRUD (scoped to a context) ----------

class SentencePayload(BaseModel):
    position: int  # 1..6
    text: str
    correct_answer: bool
    is_active: Optional[bool] = True


class SentenceResponse(BaseModel):
    id: str
    context_id: str
    position: int
    text: str
    correct_answer: bool
    is_active: bool
    created_at: str
    updated_at: str


def _sentence_to_response(s: Sentence) -> SentenceResponse:
    return SentenceResponse(
        id=s.id,
        context_id=s.context_id,
        position=s.position,
        text=s.text,
        correct_answer=s.correct_answer,
        is_active=s.is_active,
        created_at=s.created_at.isoformat(),
        updated_at=s.updated_at.isoformat(),
    )


def _validate_sentence_payload(payload: SentencePayload) -> None:
    if not 1 <= payload.position <= 6:
        raise HTTPException(status_code=400, detail="position must be in 1..6")


@router.get("/contexts/{context_id}/sentences", response_model=List[SentenceResponse])
async def list_sentences_for_context(
    context_id: str,
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    ctx_repo = ContextRepository(db)
    if not await ctx_repo.exists(context_id):
        raise HTTPException(status_code=404, detail="Context not found")
    repo = SentenceRepository(db)
    sentences = await repo.find_by_context(context_id)
    sentences.sort(key=lambda s: s.position)
    return [_sentence_to_response(s) for s in sentences]


@router.post(
    "/contexts/{context_id}/sentences",
    response_model=SentenceResponse,
    status_code=201,
)
async def create_sentence(
    context_id: str,
    payload: SentencePayload,
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    _validate_sentence_payload(payload)
    ctx_repo = ContextRepository(db)
    if not await ctx_repo.exists(context_id):
        raise HTTPException(status_code=404, detail="Context not found")
    repo = SentenceRepository(db)
    existing = await repo.find_one_by_context_position(context_id, payload.position)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Sentence already exists at position={payload.position} for this context",
        )
    sentence = Sentence.create(
        context_id=context_id,
        position=payload.position,
        text=payload.text,
        correct_answer=payload.correct_answer,
    )
    if payload.is_active is not None:
        sentence.is_active = payload.is_active
    await repo.save(sentence)
    return _sentence_to_response(sentence)


@router.put("/sentences/{sentence_id}", response_model=SentenceResponse)
async def update_sentence(
    sentence_id: str,
    payload: SentencePayload,
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    _validate_sentence_payload(payload)
    repo = SentenceRepository(db)
    sentence = await repo.get_by_id(sentence_id)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    # If position changes, ensure no collision within the same context
    if sentence.position != payload.position:
        clash = await repo.find_one_by_context_position(sentence.context_id, payload.position)
        if clash is not None and clash.id != sentence_id:
            raise HTTPException(
                status_code=409,
                detail=f"Another sentence already exists at position={payload.position}",
            )
    sentence.position = payload.position
    sentence.text = payload.text
    sentence.correct_answer = payload.correct_answer
    if payload.is_active is not None:
        sentence.is_active = payload.is_active
    sentence.updated_at = datetime.utcnow()
    await repo.save(sentence)
    return _sentence_to_response(sentence)


@router.delete("/sentences/{sentence_id}", status_code=204)
async def delete_sentence(
    sentence_id: str,
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    repo = SentenceRepository(db)
    if not await repo.exists(sentence_id):
        raise HTTPException(status_code=404, detail="Sentence not found")
    await repo.delete_by_id(sentence_id)


# ---------- Filler CRUD ----------

class FillerPayload(BaseModel):
    context_text: str
    sentence_text: str
    correct_answer: bool
    order_index: int
    is_active: Optional[bool] = True


class FillerResponse(BaseModel):
    id: str
    context_text: str
    sentence_text: str
    correct_answer: bool
    order_index: int
    is_active: bool
    created_at: str
    updated_at: str


def _filler_to_response(f: Filler) -> FillerResponse:
    return FillerResponse(
        id=f.id,
        context_text=f.context_text,
        sentence_text=f.sentence_text,
        correct_answer=f.correct_answer,
        order_index=f.order_index,
        is_active=f.is_active,
        created_at=f.created_at.isoformat(),
        updated_at=f.updated_at.isoformat(),
    )


@router.get("/fillers", response_model=List[FillerResponse])
async def list_fillers(
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    repo = FillerRepository(db)
    return [_filler_to_response(f) for f in await repo.list_all_ordered()]


@router.post("/fillers", response_model=FillerResponse, status_code=201)
async def create_filler(
    payload: FillerPayload,
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    repo = FillerRepository(db)
    filler = Filler.create(
        context_text=payload.context_text,
        sentence_text=payload.sentence_text,
        correct_answer=payload.correct_answer,
        order_index=payload.order_index,
    )
    if payload.is_active is not None:
        filler.is_active = payload.is_active
    await repo.save(filler)
    return _filler_to_response(filler)


@router.put("/fillers/{filler_id}", response_model=FillerResponse)
async def update_filler(
    filler_id: str,
    payload: FillerPayload,
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    repo = FillerRepository(db)
    filler = await repo.get_by_id(filler_id)
    if not filler:
        raise HTTPException(status_code=404, detail="Filler not found")
    filler.context_text = payload.context_text
    filler.sentence_text = payload.sentence_text
    filler.correct_answer = payload.correct_answer
    filler.order_index = payload.order_index
    if payload.is_active is not None:
        filler.is_active = payload.is_active
    filler.updated_at = datetime.utcnow()
    await repo.save(filler)
    return _filler_to_response(filler)


@router.delete("/fillers/{filler_id}", status_code=204)
async def delete_filler(
    filler_id: str,
    db: "AsyncClient" = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    repo = FillerRepository(db)
    if not await repo.exists(filler_id):
        raise HTTPException(status_code=404, detail="Filler not found")
    await repo.delete_by_id(filler_id)
