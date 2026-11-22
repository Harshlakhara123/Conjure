from pydantic import BaseModel
class ExplainFileResponse(BaseModel):
    explanation:str
    revision:int