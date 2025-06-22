from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass


class sessionObj:
    def __init__(self, database_url: str, is_async: bool = False):
        self.is_async = is_async
        self.database_url = database_url

        if self.is_async:
            self.engine = create_async_engine(database_url, echo=False)
            self.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        else:
            self.engine = create_engine(database_url, echo=False)
            self.async_session = sessionmaker(bind=self.engine)

    async def init_db(self):
        if self.is_async:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        else:
            Base.metadata.create_all(bind=self.engine)

    async def close_db(self):
        await self.engine.dispose() if self.is_async else self.engine.dispose()
