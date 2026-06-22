import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.models.user import User
from app.core.security import hash_password

class UserService:

    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def register(self, data: UserCreate) -> User:
        # check if email already exists
        existing = await self.repository.get_by_email(data.email)
        if existing:
            raise ValueError("Email already registered")

        user = User(
            id=str(uuid.uuid4()),
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )

        return await self.repository.create(user)

    async def get_by_email(self, email: str) -> User | None:
        return await self.repository.get_by_email(email)

    async def get_by_id(self, user_id: str) -> User | None:
        return await self.repository.get_by_id(user_id)