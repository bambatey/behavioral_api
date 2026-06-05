from typing import Any, Dict, List, Optional, TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.datalayer.database import get_db
from src.services import AssignmentService, ResultsService

if TYPE_CHECKING:
    from firebase_admin.firestore_async import AsyncClient


router = APIRouter(prefix="/sessions", tags=["Sessions"])


class StartSessionRequest(BaseModel):
    participant_name: str


class TrialPayload(BaseModel):
    """Slim payload from the client: only an ID + the response.
    All metadata (context, sentence, bias, correct_answer) is reconstructed
    on the server so DevTools can't surface anything sensitive."""
    trial_index: int
    sentence_id: Optional[str] = None
    filler_id: Optional[str] = None
    response: Optional[int] = None  # 1..7 Likert
    rt: Optional[float] = None


class StartSessionResponse(BaseModel):
    participant_id: str
    session_id: str
    assignment_index: int
    total_count: int
    critical_count: int
    filler_count: int


class GetTrialRequest(BaseModel):
    participant_id: str
    trial_index: int


class TrialItemResponse(BaseModel):
    context_text: str
    sentence_text: str
    sentence_id: Optional[str] = None
    filler_id: Optional[str] = None


class SubmitResultsRequest(BaseModel):
    participant_id: str
    trials: List[Dict[str, Any]]


class SubmitResultsResponse(BaseModel):
    participant_id: str
    saved_count: int


@router.post("/start", response_model=StartSessionResponse)
async def start_session(
    request: StartSessionRequest,
    db: "AsyncClient" = Depends(get_db),
) -> StartSessionResponse:
    """Allocate a Latin-square slot and return the participant's full trial list."""
    name = (request.participant_name or "").strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="participant_name is required",
        )
    try:
        service = AssignmentService(db)
        result = await service.start_session(name)
        return StartSessionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error starting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start session",
        )


@router.post("/trial", response_model=TrialItemResponse)
async def get_trial(
    request: GetTrialRequest,
    db: "AsyncClient" = Depends(get_db),
) -> TrialItemResponse:
    """Returns a single trial's render payload by index. Lets the client fetch
    trials one at a time so the full list is never visible in DevTools."""
    service = AssignmentService(db)
    trial = await service.get_trial(request.participant_id, request.trial_index)
    if trial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trial not found for this participant/index",
        )
    return TrialItemResponse(
        context_text=trial.get("context_text", ""),
        sentence_text=trial.get("sentence_text", ""),
        sentence_id=trial.get("sentence_id"),
        filler_id=trial.get("filler_id"),
    )


@router.post("/submit", response_model=SubmitResultsResponse)
async def submit_results(
    request: SubmitResultsRequest,
    db: "AsyncClient" = Depends(get_db),
) -> SubmitResultsResponse:
    """Persist trial responses for an existing participant session."""
    if not request.trials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one trial result is required",
        )
    try:
        service = ResultsService(db)
        saved = await service.submit_session(request.participant_id, request.trials)
        return SubmitResultsResponse(participant_id=request.participant_id, saved_count=saved)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error submitting results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save results",
        )
