from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session, selectinload

from app.models import AnimalProfile, AnimalProfileHistory, LivestockArchive


class ArchiveService:
    """数字化养殖档案服务，支持批次档案与牛羊个体档案 CRUD。"""

    @staticmethod
    def _parse_immunization_records(raw_value: str | None) -> dict:
        if not raw_value:
            return {"vaccines": [], "last_date": None}
        try:
            return json.loads(raw_value)
        except Exception:
            return {"vaccines": [], "last_date": None, "raw": raw_value}

    @staticmethod
    def _serialize_animal(animal: AnimalProfile) -> dict:
        return {
            "id": animal.id,
            "archive_id": animal.archive_id,
            "animal_code": animal.animal_code,
            "species": animal.species,
            "breed": animal.breed,
            "gender": animal.gender,
            "birth_date": animal.birth_date.isoformat() if animal.birth_date else None,
            "check_in_date": animal.check_in_date.isoformat() if animal.check_in_date else None,
            "weight": animal.weight,
            "health_status": animal.health_status,
            "ear_tag": animal.ear_tag,
            "source": animal.source,
            "immunization_note": animal.immunization_note,
            "notes": animal.notes,
            "is_active": animal.is_active,
            "updated_at": animal.updated_at.isoformat() if animal.updated_at else None,
            "history_records": [
                {
                    "id": record.id,
                    "field_name": record.field_name,
                    "old_value": record.old_value,
                    "new_value": record.new_value,
                    "changed_at": record.changed_at.isoformat() if record.changed_at else None,
                }
                for record in animal.history_records
            ],
        }

    @staticmethod
    def _serialize_archive(item: LivestockArchive) -> dict:
        return {
            "id": item.id,
            "batch_number": item.batch_number,
            "species": item.species,
            "quantity": item.quantity,
            "check_in_date": item.check_in_date.isoformat() if item.check_in_date else None,
            "expected_checkout_date": item.expected_checkout_date.isoformat() if item.expected_checkout_date else None,
            "immunization_records": ArchiveService._parse_immunization_records(item.immunization_records),
            "notes": item.notes,
            "average_weight": item.average_weight,
            "feed_consumption": item.feed_consumption,
            "health_status": item.health_status,
            "is_active": item.is_active,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            "animals": [ArchiveService._serialize_animal(animal) for animal in item.animal_profiles],
        }

    @staticmethod
    def _get_archive_or_raise(db: Session, archive_id: int) -> LivestockArchive:
        archive = db.query(LivestockArchive).filter(LivestockArchive.id == archive_id).first()
        if not archive:
            raise ValueError(f"Archive not found: {archive_id}")
        return archive

    @staticmethod
    def _get_animal_or_raise(db: Session, animal_id: int) -> AnimalProfile:
        animal = db.query(AnimalProfile).filter(AnimalProfile.id == animal_id).first()
        if not animal:
            raise ValueError(f"Animal profile not found: {animal_id}")
        return animal

    @staticmethod
    def get_archive_dashboard(db: Session) -> dict:
        archives = (
            db.query(LivestockArchive)
            .options(
                selectinload(LivestockArchive.animal_profiles).selectinload(AnimalProfile.history_records)
            )
            .order_by(LivestockArchive.check_in_date.desc())
            .all()
        )
        active_archives = [item for item in archives if item.is_active]
        animals = (
            db.query(AnimalProfile)
            .options(selectinload(AnimalProfile.history_records))
            .order_by(AnimalProfile.check_in_date.desc())
            .all()
        )
        individual_animals = [animal for animal in animals if animal.is_active]

        total_quantity = sum(item.quantity for item in active_archives)
        weight_values = [item.average_weight for item in active_archives if item.average_weight is not None]
        feed_values = [item.feed_consumption for item in active_archives if item.feed_consumption is not None]

        return {
            "summary": {
                "archive_count": len(archives),
                "active_batches": len(active_archives),
                "total_quantity": total_quantity,
                "average_weight": round(sum(weight_values) / len(weight_values), 2) if weight_values else None,
                "average_feed_consumption": round(sum(feed_values) / len(feed_values), 2) if feed_values else None,
                "individual_archive_count": len(individual_animals),
            },
            "archives": [ArchiveService._serialize_archive(item) for item in archives],
            "animal_profiles": [ArchiveService._serialize_animal(animal) for animal in animals],
        }

    @staticmethod
    def create_archive(
        db: Session,
        batch_number: str,
        species: str,
        quantity: int,
        check_in_date: datetime,
        expected_checkout_date: datetime | None = None,
        immunization_records: str | None = None,
        notes: str | None = None,
        average_weight: float | None = None,
        feed_consumption: float | None = None,
        health_status: str | None = None,
    ) -> dict:
        existing = db.query(LivestockArchive).filter(LivestockArchive.batch_number == batch_number).first()
        if existing:
            raise ValueError(f"Batch already exists: {batch_number}")

        archive = LivestockArchive(
            batch_number=batch_number,
            species=species,
            quantity=quantity,
            check_in_date=check_in_date,
            expected_checkout_date=expected_checkout_date,
            immunization_records=immunization_records,
            notes=notes,
            average_weight=average_weight,
            feed_consumption=feed_consumption,
            health_status=health_status or "stable",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(archive)
        db.commit()
        db.refresh(archive)
        return ArchiveService._serialize_archive(archive)

    @staticmethod
    def update_archive(
        db: Session,
        archive_id: int,
        batch_number: str | None = None,
        species: str | None = None,
        quantity: int | None = None,
        expected_checkout_date: datetime | None = None,
        immunization_records: str | None = None,
        notes: str | None = None,
        average_weight: float | None = None,
        feed_consumption: float | None = None,
        health_status: str | None = None,
        is_active: bool | None = None,
    ) -> dict:
        archive = ArchiveService._get_archive_or_raise(db, archive_id)

        if batch_number is not None and batch_number != archive.batch_number:
            existing = db.query(LivestockArchive).filter(LivestockArchive.batch_number == batch_number).first()
            if existing:
                raise ValueError(f"Batch already exists: {batch_number}")
            archive.batch_number = batch_number
        if species is not None:
            archive.species = species
        if quantity is not None:
            archive.quantity = quantity
        if expected_checkout_date is not None:
            archive.expected_checkout_date = expected_checkout_date
        if immunization_records is not None:
            archive.immunization_records = immunization_records
        if notes is not None:
            archive.notes = notes
        if average_weight is not None:
            archive.average_weight = average_weight
        if feed_consumption is not None:
            archive.feed_consumption = feed_consumption
        if health_status is not None:
            archive.health_status = health_status
        if is_active is not None:
            archive.is_active = is_active

        archive.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(archive)
        return ArchiveService._serialize_archive(archive)

    @staticmethod
    def delete_archive(db: Session, archive_id: int) -> dict:
        archive = (
            db.query(LivestockArchive)
            .options(selectinload(LivestockArchive.animal_profiles))
            .filter(LivestockArchive.id == archive_id)
            .first()
        )
        if not archive:
            raise ValueError(f"Archive not found: {archive_id}")

        archive.is_active = False
        archive.updated_at = datetime.utcnow()
        for animal in archive.animal_profiles:
            animal.is_active = False
            animal.updated_at = datetime.utcnow()

        db.commit()
        return {"id": archive.id, "is_active": archive.is_active}

    @staticmethod
    def create_animal_profile(
        db: Session,
        archive_id: int,
        animal_code: str,
        species: str,
        breed: str | None = None,
        gender: str | None = None,
        birth_date: datetime | None = None,
        check_in_date: datetime | None = None,
        weight: float | None = None,
        health_status: str | None = None,
        ear_tag: str | None = None,
        source: str | None = None,
        immunization_note: str | None = None,
        notes: str | None = None,
    ) -> dict:
        ArchiveService._get_archive_or_raise(db, archive_id)
        existing = db.query(AnimalProfile).filter(AnimalProfile.animal_code == animal_code).first()
        if existing:
            raise ValueError(f"Animal code already exists: {animal_code}")

        animal = AnimalProfile(
            archive_id=archive_id,
            animal_code=animal_code,
            species=species,
            breed=breed,
            gender=gender,
            birth_date=birth_date,
            check_in_date=check_in_date or datetime.utcnow(),
            weight=weight,
            health_status=health_status or "stable",
            ear_tag=ear_tag,
            source=source,
            immunization_note=immunization_note,
            notes=notes,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(animal)
        db.commit()
        db.refresh(animal)
        return ArchiveService._serialize_animal(animal)

    @staticmethod
    def update_animal_profile(
        db: Session,
        animal_id: int,
        animal_code: str | None = None,
        species: str | None = None,
        breed: str | None = None,
        gender: str | None = None,
        birth_date: datetime | None = None,
        check_in_date: datetime | None = None,
        weight: float | None = None,
        health_status: str | None = None,
        ear_tag: str | None = None,
        source: str | None = None,
        immunization_note: str | None = None,
        notes: str | None = None,
        is_active: bool | None = None,
    ) -> dict:
        animal = ArchiveService._get_animal_or_raise(db, animal_id)
        history_records: list[AnimalProfileHistory] = []

        if animal_code is not None and animal_code != animal.animal_code:
            existing = db.query(AnimalProfile).filter(AnimalProfile.animal_code == animal_code).first()
            if existing:
                raise ValueError(f"Animal code already exists: {animal_code}")
            animal.animal_code = animal_code
        if species is not None:
            animal.species = species
        if breed is not None:
            animal.breed = breed
        if gender is not None:
            animal.gender = gender
        if birth_date is not None:
            animal.birth_date = birth_date
        if check_in_date is not None:
            animal.check_in_date = check_in_date
        if weight is not None:
            if animal.weight != weight:
                history_records.append(
                    AnimalProfileHistory(
                        animal_id=animal.id,
                        field_name="weight",
                        old_value=str(animal.weight) if animal.weight is not None else None,
                        new_value=str(weight),
                        changed_at=datetime.utcnow(),
                        created_at=datetime.utcnow(),
                    )
                )
            animal.weight = weight
        if health_status is not None:
            animal.health_status = health_status
        if ear_tag is not None:
            if animal.ear_tag != ear_tag:
                history_records.append(
                    AnimalProfileHistory(
                        animal_id=animal.id,
                        field_name="ear_tag",
                        old_value=animal.ear_tag,
                        new_value=ear_tag,
                        changed_at=datetime.utcnow(),
                        created_at=datetime.utcnow(),
                    )
                )
            animal.ear_tag = ear_tag
        if source is not None:
            animal.source = source
        if immunization_note is not None:
            animal.immunization_note = immunization_note
        if notes is not None:
            animal.notes = notes
        if is_active is not None:
            animal.is_active = is_active

        animal.updated_at = datetime.utcnow()
        if history_records:
            db.add_all(history_records)
        db.commit()
        db.refresh(animal)
        animal = (
            db.query(AnimalProfile)
            .options(selectinload(AnimalProfile.history_records))
            .filter(AnimalProfile.id == animal_id)
            .first()
        )
        return ArchiveService._serialize_animal(animal)

    @staticmethod
    def delete_animal_profile(db: Session, animal_id: int) -> dict:
        animal = ArchiveService._get_animal_or_raise(db, animal_id)
        animal.is_active = False
        animal.updated_at = datetime.utcnow()
        db.commit()
        return {"id": animal.id, "is_active": animal.is_active}
