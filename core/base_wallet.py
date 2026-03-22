"""钱包提供方基类 - 为 Web3 钱包登录和任务执行预留接口"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class Wallet:
    provider: str
    address: str
    name: str = ""
    password: str = ""
    chain_id: str = ""
    secret_data: dict = field(default_factory=dict)
    status: str = "ready"
    created_at: int = field(default_factory=lambda: int(time.time()))


class BaseWalletProvider(ABC):
    provider: str = ""
    display_name: str = ""

    @abstractmethod
    def setup_in_browser(self, context, wallet: Wallet) -> None:
        """在浏览器上下文中准备钱包环境。"""
        ...

    @abstractmethod
    def unlock(self, page, wallet: Wallet) -> None:
        """解锁钱包或导入钱包。"""
        ...

    def connect_site(self, context, wallet: Wallet, site_origin: str) -> None:
        """连接钱包到指定站点。"""
        raise NotImplementedError(f"钱包 {self.provider} 暂未实现 connect_site")

    def sign_message(self, context, wallet: Wallet, expected_text: Optional[str] = None) -> None:
        """确认消息签名。"""
        raise NotImplementedError(f"钱包 {self.provider} 暂未实现 sign_message")

    def approve_transaction(self, context, wallet: Wallet) -> None:
        """确认链上交易。"""
        raise NotImplementedError(f"钱包 {self.provider} 暂未实现 approve_transaction")
