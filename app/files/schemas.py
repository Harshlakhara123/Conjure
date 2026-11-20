from pydantic import BaseModel,StringConstraints,field_validator,model_validator,ConfigDict
from typing import Annotated,Literal,Self
from uuid import UUID
from datetime import datetime



class FileEntryCreate(BaseModel):
    name: Annotated[str,StringConstraints(min_length=1,strip_whitespace=True)]
    type: Literal["file","folder"]
    parent_id: UUID | None = None
    content:str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls,value:str)->str:
        name=value.strip()
        if not name:
            raise ValueError("Name cannot be blank.")
        if name in {".", ".."} or "/" in name or "\\" in name:
            raise ValueError("Name must be single file or folder name")
        return name

    @model_validator(mode='after')
    def validate_folder_content(self) -> Self:
        if self.type == "folder" and self.content is not None:
            raise ValueError("Folders cant have any content")
        return self


class FileEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:UUID
    project_id:UUID
    parent_id:UUID | None = None
    name:str
    type: Literal["file","folder"]
    content:str | None = None
    updated_at:datetime