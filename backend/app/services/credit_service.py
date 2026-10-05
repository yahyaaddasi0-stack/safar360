import datetime
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.db.models import User, CreditBalance

FREE_MESSAGES_LIMIT = 5
FREE_IMAGES_LIMIT = 1

class CreditService:
    @staticmethod
    async def get_or_create_user(session, user_id: str) -> User:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user:
            user = User(id=user_id)
            balance = CreditBalance(user_id=user_id)
            session.add(user)
            session.add(balance)
            await session.commit()
            await session.refresh(user)
        return user

    @staticmethod
    async def check_credit(session, user_id: str, is_image: bool = False) -> tuple[bool, str]:
        # Check without locking first just for fast rejection
        stmt = select(CreditBalance).where(CreditBalance.user_id == user_id)
        result = await session.execute(stmt)
        balance = result.scalars().first()

        if not balance:
            await CreditService.get_or_create_user(session, user_id)
            return True, ""

        now = datetime.datetime.utcnow()
        if (now - balance.last_reset).days >= 1:
            return True, "" # Will be reset

        if is_image:
            if balance.pro_credits > 0 or balance.free_images_used < FREE_IMAGES_LIMIT:
                return True, ""
            return False, "لقد وصلت للحد الأقصى اليومي للصور المتبقية."
        else:
            if balance.pro_credits > 0 or balance.free_messages_used < FREE_MESSAGES_LIMIT:
                return True, ""
            return False, "لقد وصلت للحد الأقصى اليومي للرسائل المجانية."

    @staticmethod
    async def deduct_credit(session, user_id: str, is_image: bool = False) -> bool:
        # Pessimistic lock
        stmt = select(CreditBalance).where(CreditBalance.user_id == user_id).with_for_update()
        result = await session.execute(stmt)
        balance = result.scalars().first()

        if not balance:
            return False

        now = datetime.datetime.utcnow()
        if (now - balance.last_reset).days >= 1:
            balance.free_messages_used = 0
            balance.free_images_used = 0
            balance.last_reset = now

        if is_image:
            if balance.pro_credits > 0:
                balance.pro_credits -= 1
            elif balance.free_images_used < FREE_IMAGES_LIMIT:
                balance.free_images_used += 1
            else:
                return False
        else:
            if balance.pro_credits > 0:
                balance.pro_credits -= 1
            elif balance.free_messages_used < FREE_MESSAGES_LIMIT:
                balance.free_messages_used += 1
            else:
                return False

        await session.commit()
        return True

    @staticmethod
    async def add_pro_credits(session, user_id: str, amount: int) -> bool:
        stmt = select(CreditBalance).where(CreditBalance.user_id == user_id).with_for_update()
        result = await session.execute(stmt)
        balance = result.scalars().first()

        if not balance:
            await CreditService.get_or_create_user(session, user_id)
            stmt = select(CreditBalance).where(CreditBalance.user_id == user_id).with_for_update()
            result = await session.execute(stmt)
            balance = result.scalars().first()

        balance.pro_credits += amount

        stmt_user = select(User).where(User.id == user_id).with_for_update()
        user_res = await session.execute(stmt_user)
        user = user_res.scalars().first()
        if user:
            user.is_pro = True

        await session.commit()
        return True
