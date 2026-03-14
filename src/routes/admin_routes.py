from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

from datalayer.database import get_db
from datalayer.model import Participant
from middleware import verify_jwt_token
from services import ResultsService, ExportService

router = APIRouter(prefix="/admin", tags=["Admin"])


class ParticipantInfo(BaseModel):
    id: str
    name: str
    test_type: str
    session_id: str
    created_at: str
    trial_count: int


class TrialInfo(BaseModel):
    id: str
    trial_index: int
    rt: float | None = None
    response: str | None = None
    task_type: str | None = None
    sentence_id: str | None = None
    word: str | None = None
    word_position: int | None = None
    condition: str | None = None
    sentence: str | None = None
    is_grammatical: bool | None = None
    attrition_marker: str | None = None
    accuracy: int | None = None
    correct_answer: str | None = None


class ParticipantDetailsResponse(BaseModel):
    participant: ParticipantInfo
    trials: List[TrialInfo]


@router.get("/participants", response_model=List[ParticipantInfo])
async def list_participants(
    db: AsyncClient = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
) -> List[ParticipantInfo]:
    """
    Get list of all participants.
    Requires Firebase authentication.
    """
    try:
        service = ResultsService(db)
        participants = await service.get_all_participants()

        result = []
        for p in participants:
            trial_count = await service.trial_repo.count_by_participant(p.id)
            result.append(
                ParticipantInfo(
                    id=p.id,
                    name=p.name,
                    test_type=p.test_type,
                    session_id=p.session_id,
                    created_at=p.created_at.isoformat(),
                    trial_count=trial_count,
                )
            )

        # Sort by created_at descending (newest first)
        result.sort(key=lambda x: x.created_at, reverse=True)
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error listing participants: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve participants",
        )


@router.get("/participants/{participant_id}", response_model=ParticipantDetailsResponse)
async def get_participant_results(
    participant_id: str,
    db: AsyncClient = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
) -> ParticipantDetailsResponse:
    """
    Get detailed results for a specific participant.
    Requires Firebase authentication.
    """
    try:
        service = ResultsService(db)
        result = await service.get_participant_results(participant_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participant not found",
            )

        participant = result["participant"]
        trials = result["trials"]

        return ParticipantDetailsResponse(
            participant=ParticipantInfo(
                id=participant.id,
                name=participant.name,
                test_type=participant.test_type,
                session_id=participant.session_id,
                created_at=participant.created_at.isoformat(),
                trial_count=len(trials),
            ),
            trials=[
                TrialInfo(
                    id=t.id,
                    trial_index=t.trial_index,
                    rt=t.rt,
                    response=t.response,
                    task_type=t.task_type,
                    sentence_id=t.sentence_id,
                    word=t.word,
                    word_position=t.word_position,
                    condition=t.condition,
                    sentence=t.sentence,
                    is_grammatical=t.is_grammatical,
                    attrition_marker=t.attrition_marker,
                    accuracy=t.accuracy,
                    correct_answer=t.correct_answer,
                )
                for t in trials
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting participant results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve results",
        )


@router.get("/export")
async def export_all_results(
    db: AsyncClient = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    """
    Export all test results to Excel.
    Requires Firebase authentication.
    """
    try:
        service = ExportService(db)
        excel_bytes = await service.export_to_excel()

        return FileResponse(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="all_results.xlsx",
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error exporting results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export results",
        )


@router.get("/export/{participant_id}")
async def export_participant_results(
    participant_id: str,
    db: AsyncClient = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
):
    """
    Export results for a specific participant to Excel.
    Requires Firebase authentication.
    """
    try:
        service = ExportService(db)
        excel_bytes = await service.export_to_excel(participant_id)

        # Verify participant exists
        participant = await service.participant_repo.get_by_id(participant_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participant not found",
            )

        filename = f"{participant.name}_results.xlsx".replace(" ", "_")

        return FileResponse(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error exporting participant results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export results",
        )


@router.get("/stats")
async def get_statistics(
    db: AsyncClient = Depends(get_db),
    token: dict = Depends(verify_jwt_token),
) -> Dict[str, Any]:
    """
    Get aggregate statistics from all test results.
    Requires Firebase authentication.
    """
    try:
        service = ResultsService(db)
        all_trials = await service.trial_repo.get_all()

        if not all_trials:
            return {
                "total_participants": 0,
                "total_trials": 0,
                "spr_count": 0,
                "gj_count": 0,
                "avg_rt": None,
                "avg_accuracy": None,
            }

        # Calculate statistics
        spr_trials = [t for t in all_trials if t.test_type == "spr"]
        gj_trials = [t for t in all_trials if t.test_type == "gj"]

        rts = [t.rt for t in all_trials if t.rt is not None]
        avg_rt = sum(rts) / len(rts) if rts else None

        accuracies = [t.accuracy for t in all_trials if t.accuracy is not None]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else None

        participants = await service.get_all_participants()
        unique_participant_ids = {p.id for p in participants}

        return {
            "total_participants": len(unique_participant_ids),
            "total_trials": len(all_trials),
            "spr_count": len(spr_trials),
            "gj_count": len(gj_trials),
            "avg_rt": round(avg_rt, 2) if avg_rt else None,
            "avg_accuracy": round(avg_accuracy, 2) if avg_accuracy else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error calculating statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate statistics",
        )
