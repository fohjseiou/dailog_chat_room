import pytest
from app.models.user_preference import UserPreference

@pytest.mark.asyncio
async def test_user_preference_creation(db_session, test_user):
    pref = UserPreference(
        user_id=test_user.id,
        key="response_style",
        value="detailed"
    )
    db_session.add(pref)
    await db_session.commit()
    await db_session.refresh(pref)

    assert pref.id is not None
    assert pref.key == "response_style"
    assert pref.value == "detailed"

@pytest.mark.asyncio
async def test_user_preference_unique_per_user_key(db_session, test_user):
    pref1 = UserPreference(user_id=test_user.id, key="theme", value="dark")
    db_session.add(pref1)
    await db_session.commit()

    pref2 = UserPreference(user_id=test_user.id, key="theme", value="light")
    db_session.add(pref2)

    with pytest.raises(Exception):  # IntegrityError
        await db_session.commit()
