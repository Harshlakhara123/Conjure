from datetime import datetime
from pydantic import BaseModel, ConfigDict , StringConstraints
from typing import Annotated
from uuid import UUID

class ProjectCreate(BaseModel):
    name: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

class ProjectRename(BaseModel):
    name: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]