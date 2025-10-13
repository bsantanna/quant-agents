from app.infrastructure.auth.schema import User


async def map_user(userinfo: dict) -> User | None: #NOSONAR: must use async to register with middleware
    user_id = userinfo.get("sub")
    if user_id is not None:
        return User(
            id=f"id_{user_id}",
            email=userinfo.get("email"),
            username=userinfo.get("preferred_username"),
        )
    return None
