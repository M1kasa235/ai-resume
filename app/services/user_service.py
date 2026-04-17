# app/services/user_service.py
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """通过ID获取用户"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreate) -> User:
        """创建新用户"""
        # 检查用户名是否已存在
        if await self.get_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 检查邮箱是否已存在
        if await self.get_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

        # 创建用户对象
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            phone=user_data.phone,
            hashed_password=get_password_hash(user_data.password),
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """验证用户登录"""
        # 支持用户名或邮箱登录
        result = await self.db.execute(
            select(User).where(
                or_(User.username == username, User.email == username)
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None

        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        await self.db.commit()

        return user

    async def update_profile(self, user: User, update_data: UserUpdate) -> User:
        """更新用户资料"""
        update_dict = update_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_password(self, user: User, old_password: str, new_password: str) -> bool:
        """修改密码"""
        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误"
            )

        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        return True

    async def list_users(self, skip: int = 0, limit: int = 100) -> tuple:
        """获取用户列表（管理员用）"""
        from sqlalchemy import func

        # 查询总数
        count_result = await self.db.execute(select(func.count()).select_from(User))
        total = count_result.scalar()

        # 查询列表
        result = await self.db.execute(
            select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        )
        users = result.scalars().all()

        return total, users