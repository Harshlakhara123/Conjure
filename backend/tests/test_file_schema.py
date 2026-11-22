from app.files.schemas import FileEntryCreate,FileEntryRename
from pydantic import ValidationError
import pytest

def test_create_trims_entry_name():
    test_file = FileEntryCreate(
        name="  main.py  ",
        type="file"
    )
    assert test_file.name == "main.py"

def test_rename_rejects_name_over_byte_limit():
    with pytest.raises(ValidationError, match="at most 255 UTF-8 bytes"):
        FileEntryRename(name="é" * 128,expected_revision=1)