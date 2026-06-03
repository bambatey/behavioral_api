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
    trial_index: int
    is_filler: bool
    context_id: Optional[str] = None
    context_text: Optional[str] = None
    sentence_id: Optional[str] = None
    sentence_text: Optional[str] = None
    filler_id: Optional[str] = None
    bias: Optional[str] = None
    position: Optional[int] = None
    correct_answer: Optional[bool] = None
    response: Optional[int] = None  # 1..7 Likert
    rt: Optional[float] = None


class StartSessionResponse(BaseModel):
    participant_id: str
    session_id: str
    assignment_index: int
    trials: List[Dict[str, Any]]
    critical_count: int
    filler_count: int


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
