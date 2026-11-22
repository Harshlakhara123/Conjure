from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator, AfterValidator
from typing import Annotated,Literal,Self
from uuid import UUID
from datetime import datetime

MAX_ENTRY_NAME_BYTES = 255
def validate_entry_name(name: str) -> str:
    if name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError("Name must be single file or folder name")
    if len(name.encode("utf-8")) > MAX_ENTRY_NAME_BYTES:
        raise ValueError("Name must be at most 255 UTF-8 bytes.")
    return name

EntryName = Annotated[
    str,
    StringConstraints(min_length=1, strip_whitespace=True),
    AfterValidator(validate_entry_name),
]
class FileEntryCreate(BaseModel):
    name: EntryName
    type: Literal["file","folder"]
    parent_id: UUID | None = None
    content:str | None = None

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
    revision: int

class FileContentUpdate(BaseModel):
    content: str
    expected_revision: int = Field(ge=1, strict=True)

class FileEntryRename(BaseModel):
    name:EntryName
    expected_revision: int = Field(ge=1, strict=True)
