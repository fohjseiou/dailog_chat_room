from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.services.memory_service import MemoryService
from app.schemas.preference import PreferenceCreate, PreferenceUpdate, PreferenceResponse, PreferencesResponse
from app.dependencies import get_current_user_dep
from app.models.user import User

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=PreferencesResponse)
async def get_all_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """
    Get all preferences for the current authenticated user.

    Returns a dictionary of all preference key-value pairs.
    """
    service = MemoryService(db)
    preferences = await service.get_preferences(user_id=str(current_user.id))

    return PreferencesResponse(
        user_id=str(current_user.id),
        preferences=preferences
    )


@router.post("", response_model=PreferenceResponse)
async def set_preference(
    data: PreferenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """
    Set or update a preference for the current authenticated user.

    If the preference key already exists, it will be updated.
    If it doesn't exist, it will be created.

    Common preference keys:
    - language: Preferred language (e.g., "zh-CN", "en-US")
    - response_style: How responses should be formatted (e.g., "concise", "detailed")
    - theme: UI theme preference (e.g., "light", "dark")
    - notifications: Email notification settings (e.g., "on", "off")
    """
    from app.models.user_preference import UserPreference
    from sqlalchemy import select, and_

    service = MemoryService(db)
    await service.set_preference(
        user_id=str(current_user.id),
        key=data.key,
        value=data.value
    )

    # Fetch the created/updated preference to return
    result = await db.execute(
        select(UserPreference).where(
            and_(
                UserPreference.user_id == str(current_user.id),
                UserPreference.key == data.key
            )
        )
    )
    preference = result.scalar_one_or_none()

    if not preference:
        raise HTTPException(status_code=500, detail="Failed to create preference")

    return preference


@router.put("/{key}", response_model=PreferenceResponse)
async def update_preference(
    key: str,
    data: PreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """
    Update an existing preference value.

    Returns 404 if the preference key doesn't exist for this user.
    Use POST /preferences to create new preferences.
    """
    from app.models.user_preference import UserPreference
    from sqlalchemy import select, and_

    # Check if preference exists
    result = await db.execute(
        select(UserPreference).where(
            and_(
                UserPreference.user_id == str(current_user.id),
                UserPreference.key == key
            )
        )
    )
    preference = result.scalar_one_or_none()

    if not preference:
        raise HTTPException(
            status_code=404,
            detail=f"Preference '{key}' not found. Use POST to create it."
        )

    # Update using the service
    service = MemoryService(db)
    await service.set_preference(
        user_id=str(current_user.id),
        key=key,
        value=data.value
    )

    # Fetch updated preference
    await db.refresh(preference)
    return preference


@router.delete("/{key}")
async def delete_preference(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """
    Delete a preference by key.

    Returns success message even if the key doesn't exist (idempotent).
    """
    from app.models.user_preference import UserPreference
    from sqlalchemy import delete, and_
    import logging

    logger = logging.getLogger(__name__)

    await db.execute(
        delete(UserPreference).where(
            and_(
                UserPreference.user_id == str(current_user.id),
                UserPreference.key == key
            )
        )
    )
    await db.commit()

    logger.info(f"Deleted preference {key} for user {current_user.id}")
    return {"message": f"Preference '{key}' deleted"}


@router.get("/keys", response_model=List[str])
async def list_preference_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """
    List all preference keys for the current user.

    Returns a list of keys without their values.
    Useful for UI to show what preferences are set.
    """
    from app.models.user_preference import UserPreference
    from sqlalchemy import select

    result = await db.execute(
        select(UserPreference.key).where(UserPreference.user_id == str(current_user.id))
    )
    keys = result.scalars().all()

    return list(keys)
