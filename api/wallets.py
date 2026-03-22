from datetime import datetime, timezone
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from core.db import WalletModel, get_session

router = APIRouter(prefix="/wallets", tags=["wallets"])


class WalletCreate(BaseModel):
    name: str
    provider: str = "metamask"
    address: str
    chain_id: str = ""
    password: str = ""
    secret_data: dict = Field(default_factory=dict)


class WalletUpdate(BaseModel):
    name: Optional[str] = None
    chain_id: Optional[str] = None
    password: Optional[str] = None
    secret_data: Optional[dict] = None
    status: Optional[str] = None


@router.get("")
def list_wallets(session: Session = Depends(get_session)):
    return session.exec(select(WalletModel).order_by(WalletModel.id.desc())).all()


@router.post("")
def create_wallet(body: WalletCreate, session: Session = Depends(get_session)):
    wallet = WalletModel(
        name=body.name,
        provider=body.provider,
        address=body.address,
        chain_id=body.chain_id,
        password=body.password,
        secret_json=json.dumps(body.secret_data or {}, ensure_ascii=False),
    )
    session.add(wallet)
    session.commit()
    session.refresh(wallet)
    return wallet


@router.get("/{wallet_id}")
def get_wallet(wallet_id: int, session: Session = Depends(get_session)):
    wallet = session.get(WalletModel, wallet_id)
    if not wallet:
        raise HTTPException(404, "钱包不存在")
    return wallet


@router.patch("/{wallet_id}")
def update_wallet(wallet_id: int, body: WalletUpdate, session: Session = Depends(get_session)):
    wallet = session.get(WalletModel, wallet_id)
    if not wallet:
        raise HTTPException(404, "钱包不存在")
    if body.name is not None:
        wallet.name = body.name
    if body.chain_id is not None:
        wallet.chain_id = body.chain_id
    if body.password is not None:
        wallet.password = body.password
    if body.secret_data is not None:
        wallet.secret_json = json.dumps(body.secret_data, ensure_ascii=False)
    if body.status is not None:
        wallet.status = body.status
    wallet.updated_at = datetime.now(timezone.utc)
    session.add(wallet)
    session.commit()
    session.refresh(wallet)
    return wallet
