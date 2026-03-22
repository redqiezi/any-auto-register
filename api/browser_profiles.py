from datetime import datetime, timezone
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from core.browser_profiles import ensure_profile_dir
from core.db import BrowserProfileModel, WalletModel, get_session

router = APIRouter(prefix="/browser-profiles", tags=["browser-profiles"])


class BrowserProfileCreate(BaseModel):
    name: str
    wallet_id: Optional[int] = None
    proxy: str = ""
    browser_type: str = "chromium"
    fingerprint: dict = Field(default_factory=dict)
    extension_paths: list[str] = Field(default_factory=list)


class BrowserProfileUpdate(BaseModel):
    name: Optional[str] = None
    wallet_id: Optional[int] = None
    proxy: Optional[str] = None
    browser_type: Optional[str] = None
    fingerprint: Optional[dict] = None
    extension_paths: Optional[list[str]] = None
    status: Optional[str] = None


@router.get("")
def list_browser_profiles(session: Session = Depends(get_session)):
    return session.exec(
        select(BrowserProfileModel).order_by(BrowserProfileModel.id.desc())
    ).all()


@router.post("")
def create_browser_profile(body: BrowserProfileCreate, session: Session = Depends(get_session)):
    if body.wallet_id is not None and not session.get(WalletModel, body.wallet_id):
        raise HTTPException(404, "绑定的钱包不存在")
    profile = BrowserProfileModel(
        name=body.name,
        wallet_id=body.wallet_id,
        proxy=body.proxy,
        browser_type=body.browser_type,
        fingerprint_json=json.dumps(body.fingerprint or {}, ensure_ascii=False),
        extension_paths_json=json.dumps(body.extension_paths or [], ensure_ascii=False),
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    if not profile.user_data_dir:
        profile.user_data_dir = ensure_profile_dir(profile.id)
        profile.updated_at = datetime.now(timezone.utc)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


@router.get("/{profile_id}")
def get_browser_profile(profile_id: int, session: Session = Depends(get_session)):
    profile = session.get(BrowserProfileModel, profile_id)
    if not profile:
        raise HTTPException(404, "浏览器 Profile 不存在")
    return profile


@router.patch("/{profile_id}")
def update_browser_profile(profile_id: int, body: BrowserProfileUpdate,
                           session: Session = Depends(get_session)):
    profile = session.get(BrowserProfileModel, profile_id)
    if not profile:
        raise HTTPException(404, "浏览器 Profile 不存在")
    if body.wallet_id is not None and not session.get(WalletModel, body.wallet_id):
        raise HTTPException(404, "绑定的钱包不存在")
    if body.name is not None:
        profile.name = body.name
    if body.wallet_id is not None:
        profile.wallet_id = body.wallet_id
    if body.proxy is not None:
        profile.proxy = body.proxy
    if body.browser_type is not None:
        profile.browser_type = body.browser_type
    if body.fingerprint is not None:
        profile.fingerprint_json = json.dumps(body.fingerprint, ensure_ascii=False)
    if body.extension_paths is not None:
        profile.extension_paths_json = json.dumps(body.extension_paths, ensure_ascii=False)
    if body.status is not None:
        profile.status = body.status
    profile.updated_at = datetime.now(timezone.utc)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile
