"""平台插件基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import time


class AccountStatus(str, Enum):
    REGISTERED = "registered"
    TRIAL = "trial"
    SUBSCRIBED = "subscribed"
    EXPIRED = "expired"
    INVALID = "invalid"


@dataclass
class Account:
    platform: str
    email: str
    password: str
    user_id: str = ""
    region: str = ""
    token: str = ""
    status: AccountStatus = AccountStatus.REGISTERED
    trial_end_time: int = 0
    extra: dict = field(default_factory=dict)
    created_at: int = field(default_factory=lambda: int(time.time()))


@dataclass
class RegisterConfig:
    """注册任务配置"""
    executor_type: str = "protocol"
    captcha_solver: str = "yescaptcha"
    proxy: Optional[str] = None
    user_data_dir: Optional[str] = None
    browser_profile_id: Optional[int] = None
    extra: dict = field(default_factory=dict)


class BasePlatform(ABC):
    name: str = ""
    display_name: str = ""
    version: str = "1.0.0"
    supported_executors: list = ["protocol", "headless", "headed"]

    def __init__(self, config: RegisterConfig = None):
        self.config = config or RegisterConfig()
        if self.config.executor_type not in self.supported_executors:
            raise NotImplementedError(
                f"{self.display_name} 暂不支持 '{self.config.executor_type}' 执行器，"
                f"当前支持: {self.supported_executors}"
            )

    @abstractmethod
    def register(self, email: str, password: str = None) -> Account:
        """执行注册流程，返回 Account"""
        ...

    @abstractmethod
    def check_valid(self, account: Account) -> bool:
        """检测账号是否有效"""
        ...

    def get_trial_url(self, account: Account) -> Optional[str]:
        """生成试用激活链接（可选实现）"""
        return None

    def get_platform_actions(self) -> list:
        """
        返回平台支持的额外操作列表，每项格式:
        {"id": str, "label": str, "params": [{"key": str, "label": str, "type": str}]}
        """
        return []

    def supports_wallet_login(self) -> bool:
        """声明平台是否支持钱包登录。"""
        return False

    def get_supported_task_types(self) -> list[str]:
        """返回平台支持的平台任务类型。"""
        return []

    def login_with_wallet(self, session, wallet, params: dict | None = None) -> dict:
        """执行钱包登录，后续由 web3 平台按需实现。"""
        raise NotImplementedError(f"平台 {self.name} 不支持钱包登录")

    def run_task(self, session, wallet=None, account: Account = None,
                 task_type: str = "", params: dict | None = None) -> dict:
        """执行平台任务，后续可用于签到、mint、验证等场景。"""
        raise NotImplementedError(f"平台 {self.name} 不支持平台任务: {task_type}")

    def execute_action(self, action_id: str, account: Account, params: dict) -> dict:
        """
        执行平台特定操作，返回 {"ok": bool, "data": any, "error": str}
        """
        raise NotImplementedError(f"平台 {self.name} 不支持操作: {action_id}")

    def get_quota(self, account: Account) -> dict:
        """查询账号配额（可选实现）"""
        return {}

    def _make_executor(self):
        """根据 config 创建执行器"""
        from .executors.protocol import ProtocolExecutor
        t = self.config.executor_type
        if t == "protocol":
            return ProtocolExecutor(proxy=self.config.proxy)
        elif t == "headless":
            from .executors.playwright import PlaywrightExecutor
            return PlaywrightExecutor(
                proxy=self.config.proxy,
                headless=True,
                user_data_dir=self.config.user_data_dir,
            )
        elif t == "headed":
            from .executors.playwright import PlaywrightExecutor
            return PlaywrightExecutor(
                proxy=self.config.proxy,
                headless=False,
                user_data_dir=self.config.user_data_dir,
            )
        raise ValueError(f"未知执行器类型: {t}")

    def _make_captcha(self, **kwargs):
        """根据 config 创建验证码解决器"""
        from .base_captcha import YesCaptcha, ManualCaptcha, LocalSolverCaptcha
        t = self.config.captcha_solver
        if t == "yescaptcha":
            key = kwargs.get("key") or self.config.extra.get("yescaptcha_key", "")
            return YesCaptcha(key)
        elif t == "manual":
            return ManualCaptcha()
        elif t == "local_solver":
            url = self.config.extra.get("solver_url", "http://localhost:8888")
            return LocalSolverCaptcha(url)
        raise ValueError(f"未知验证码解决器: {t}")
