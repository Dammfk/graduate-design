import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import AnimalProfileCreate, AnimalProfileUpdate, LivestockArchiveCreate, LivestockArchiveUpdate
from app.services import ArchiveService

router = APIRouter(prefix="/api/v1/archives", tags=["archives"])


@router.get("/dashboard")
async def get_archive_dashboard(db: Session = Depends(get_db)):
    try:
        return {"status": "success", "data": ArchiveService.get_archive_dashboard(db)}
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/")
async def create_archive(payload: LivestockArchiveCreate, db: Session = Depends(get_db)):
    try:
        result = ArchiveService.create_archive(
            db=db,
            batch_number=payload.batch_number,
            species=payload.species,
            quantity=payload.quantity,
            check_in_date=payload.check_in_date,
            expected_checkout_date=payload.expected_checkout_date,
            immunization_records=payload.immunization_records,
            notes=payload.notes,
            average_weight=payload.average_weight,
            feed_consumption=payload.feed_consumption,
            health_status=payload.health_status,
        )
        return {"status": "success", "message": "Archive created", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.put("/{archive_id}")
async def update_archive(
    archive_id: int,
    payload: LivestockArchiveUpdate,
    db: Session = Depends(get_db),
):
    try:
        result = ArchiveService.update_archive(
            db=db,
            archive_id=archive_id,
            batch_number=payload.batch_number,
            species=payload.species,
            quantity=payload.quantity,
            expected_checkout_date=payload.expected_checkout_date,
            immunization_records=payload.immunization_records,
            notes=payload.notes,
            average_weight=payload.average_weight,
            feed_consumption=payload.feed_consumption,
            health_status=payload.health_status,
            is_active=payload.is_active,
        )
        return {"status": "success", "message": "Archive updated", "data": result}
    except ValueError as exc:
        detail = str(exc)
        code = status.HTTP_400_BAD_REQUEST if "already exists" in detail else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=detail)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.delete("/{archive_id}")
async def delete_archive(archive_id: int, db: Session = Depends(get_db)):
    try:
        result = ArchiveService.delete_archive(db=db, archive_id=archive_id)
        return {"status": "success", "message": "Archive deleted", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/animals")
async def create_animal_profile(payload: AnimalProfileCreate, db: Session = Depends(get_db)):
    try:
        result = ArchiveService.create_animal_profile(
            db=db,
            archive_id=payload.archive_id,
            animal_code=payload.animal_code,
            species=payload.species,
            breed=payload.breed,
            gender=payload.gender,
            birth_date=payload.birth_date,
            check_in_date=payload.check_in_date,
            weight=payload.weight,
            health_status=payload.health_status,
            ear_tag=payload.ear_tag,
            source=payload.source,
            immunization_note=payload.immunization_note,
            notes=payload.notes,
        )
        return {"status": "success", "message": "Animal profile created", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.put("/animals/{animal_id}")
async def update_animal_profile(
    animal_id: int,
    payload: AnimalProfileUpdate,
    db: Session = Depends(get_db),
):
    try:
        result = ArchiveService.update_animal_profile(
            db=db,
            animal_id=animal_id,
            animal_code=payload.animal_code,
            species=payload.species,
            breed=payload.breed,
            gender=payload.gender,
            birth_date=payload.birth_date,
            check_in_date=payload.check_in_date,
            weight=payload.weight,
            health_status=payload.health_status,
            ear_tag=payload.ear_tag,
            source=payload.source,
            immunization_note=payload.immunization_note,
            notes=payload.notes,
            is_active=payload.is_active,
        )
        return {"status": "success", "message": "Animal profile updated", "data": result}
    except ValueError as exc:
        detail = str(exc)
        code = status.HTTP_400_BAD_REQUEST if "already exists" in detail else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=detail)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.delete("/animals/{animal_id}")
async def delete_animal_profile(animal_id: int, db: Session = Depends(get_db)):
    try:
        result = ArchiveService.delete_animal_profile(db=db, animal_id=animal_id)
        return {"status": "success", "message": "Animal profile deleted", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
