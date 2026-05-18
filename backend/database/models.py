from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, create_engine

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    username: str
    hashed_password: str
    account_type: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

engine = create_engine("sqlite:///.data", echo=False)
SQLModel.metadata.create_all(engine)