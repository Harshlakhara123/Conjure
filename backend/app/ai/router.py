from fastapi import APIRouter,Depends,HTTPException
from uuid import UUID
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from asyncio import wait_for

from app.auth.clerk import require_clerk_user
from app.db_session import get_db_session

from app.ai.schemas import ExplainFileResponse
from app.users.repository import UserRepository
from app.projects.repository import ProjectRepository
from app.ai.file_context import load_file_context
from app.ai.service import get_explain_graph

router = APIRouter(prefix="/projects/{project_id}/files")
MAX_EXPLAIN_SOURCE_BYTES = 8 * 1024
EXPLAIN_TIMEOUT_SECONDS = 90

@router.post("/{entry_id}/explain", response_model=ExplainFileResponse)
async def explain_file(
    project_id:UUID,
    entry_id:UUID,
    clerk_user_id:Annotated[str,Depends(require_clerk_user)],
    session:Annotated[AsyncSession,Depends(get_db_session)]
) -> ExplainFileResponse:
    async with session.begin():
        file_context = await load_file_context(
            session=session,
            clerk_user_id=clerk_user_id,
            project_id=project_id,
            entry_id=entry_id
        )
    if file_context is None:
        raise HTTPException(status_code=404,detail="File not found")
    if len(file_context.content.encode("utf-8")) > MAX_EXPLAIN_SOURCE_BYTES:
        raise HTTPException(status_code=422,detail="This file exceeds the 8 KiB limit for Explain File.")
    graph = get_explain_graph()
    try:
        result = await wait_for(
            graph.ainvoke({'name':file_context.name,'content':file_context.content}),
            timeout=EXPLAIN_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        raise HTTPException(status_code=504,detail="AI took longer than expected")
    return ExplainFileResponse(
        explanation=result['explanation'],
        revision=file_context.revision
    )