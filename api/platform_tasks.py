from datetime import datetime, timezone
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from core.db import (
    AccountModel,
    BrowserProfileModel,
    PlatformTaskModel,
    WalletModel,
    get_session,
)
from core.registry import get

router = APIRouter(prefix="/platform-tasks", tags=["platform-tasks"])


class PlatformTaskCreate(BaseModel):
    platform: str
    task_type: str
    profile_id: int | None = None
    wallet_id: int | None = None
    account_id: int | None = None
    params: dict = Field(default_factory=dict)


@router.get("")
def list_platform_tasks(session: Session = Depends(get_session)):
    return session.exec(select(PlatformTaskModel).order_by(PlatformTaskModel.id.desc())).all()


@router.post("")
def create_platform_task(body: PlatformTaskCreate, session: Session = Depends(get_session)):
    PlatformCls = get(body.platform)
    platform = PlatformCls()
    supported = set(platform.get_supported_task_types())
    if supported and body.task_type not in supported:
        raise HTTPException(400, f"平台不支持任务类型: {body.task_type}")
    if body.profile_id is not None and not session.get(BrowserProfileModel, body.profile_id):
        raise HTTPException(404, "浏览器 Profile 不存在")
    if body.wallet_id is not None and not session.get(WalletModel, body.wallet_id):
        raise HTTPException(404, "钱包不存在")
    if body.account_id is not None and not session.get(AccountModel, body.account_id):
        raise HTTPException(404, "账号不存在")

    task = PlatformTaskModel(
        platform=body.platform,
        task_type=body.task_type,
        profile_id=body.profile_id,
        wallet_id=body.wallet_id,
        account_id=body.account_id,
        status="draft",
        params_json=json.dumps(body.params or {}, ensure_ascii=False),
        result_json=json.dumps({
            "message": "第一阶段骨架：任务记录已创建，执行器待接入",
        }, ensure_ascii=False),
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.get("/{task_id}")
def get_platform_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(PlatformTaskModel, task_id)
    if not task:
        raise HTTPException(404, "平台任务不存在")
    return task


@router.post("/{task_id}/mark-running")
def mark_platform_task_running(task_id: int, session: Session = Depends(get_session)):
    task = session.get(PlatformTaskModel, task_id)
    if not task:
        raise HTTPException(404, "平台任务不存在")
    task.status = "running"
    task.updated_at = datetime.now(timezone.utc)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task
