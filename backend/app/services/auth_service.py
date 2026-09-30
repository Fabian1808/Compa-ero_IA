import msal
import httpx
import json
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.user import User
from app.models.account import Account, AccountStatus
from app.security.encryption import get_encryption
from app.database import Base
import uuid


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._msal_app: Optional[msal.PublicClientApplication] = None

    @property
    def msal_app(self) -> msal.PublicClientApplication:
        if self._msal_app is None:
            self._msal_app = msal.PublicClientApplication(
                client_id=settings.ms_graph_client_id,
                
                authority=settings.ms_graph_authority,
            )
        return self._msal_app

    async def initiate_device_code_flow(self) -> dict:
        """Initiate device code flow for Microsoft OAuth."""
        flow = self.msal_app.initiate_device_flow(scopes=settings.ms_graph_scopes_list)
        if "user_code" not in flow:
            raise Exception("Failed to initiate device code flow")

        return {
            "device_code": flow["device_code"],
            "user_code": flow["user_code"],
            "verification_uri": flow["verification_uri"],
            "expires_in": flow["expires_in"],
            "interval": flow["interval"],
            "message": flow["message"],
        }

    async def acquire_token_by_device_flow(self, device_code: str) -> dict:
        """Complete device code flow and acquire tokens."""
        result = self.msal_app.acquire_token_by_device_flow({"device_code": device_code})

        if "access_token" not in result:
            error = result.get("error")
            error_description = result.get("error_description")
            raise Exception(f"Token acquisition failed: {error} - {error_description}")

        return result

    async def get_or_create_user_from_token(self, access_token: str) -> User:
        """Get user info from Microsoft Graph and create/update local user."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            graph_user = response.json()

        user_id = graph_user["id"]
        email = graph_user.get("userPrincipalName") or graph_user.get("mail")
        name = graph_user.get("displayName") or email

        # Check if user exists
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                id=user_id,
                email=email,
                name=name,
                avatar_url=None,
                preferences_json="{}"
            )
            self.db.add(user)
            await self.db.flush()

        return user

    async def store_account_tokens(self, user: User, token_result: dict) -> Account:
        """Store encrypted tokens for the account."""
        encryption = get_encryption(user.id)

        access_token = token_result["access_token"]
        refresh_token = token_result.get("refresh_token", "")
        expires_in = token_result.get("expires_in", 3600)
        token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        # Check if account exists
        result = await self.db.execute(
            select(Account).where(
                Account.user_id == user.id,
                Account.provider == "microsoft",
                Account.provider_account_id == user.id
            )
        )
        account = result.scalar_one_or_none()

        if account is None:
            account = Account(
                id=str(uuid.uuid4()),
                user_id=user.id,
                provider="microsoft",
                provider_account_id=user.id,
                encrypted_access_token=encryption.encrypt(access_token),
                encrypted_refresh_token=encryption.encrypt(refresh_token),
                token_expires_at=token_expires_at,
                scopes=json.dumps(settings.ms_graph_scopes_list),
                status=AccountStatus.ACTIVE,
                meta="{}"
            )
            self.db.add(account)
        else:
            account.encrypted_access_token = encryption.encrypt(access_token)
            account.encrypted_refresh_token = encryption.encrypt(refresh_token)
            account.token_expires_at = token_expires_at
            account.status = AccountStatus.ACTIVE

        await self.db.flush()
        return account

    async def get_valid_access_token(self, account: Account) -> str:
        """Get valid access token, refreshing if necessary."""
        encryption = get_encryption(account.user_id)

        if account.token_expires_at > datetime.utcnow() + timedelta(minutes=5):
            return encryption.decrypt(account.encrypted_access_token)

        # Refresh token
        refresh_token = encryption.decrypt(account.encrypted_refresh_token)
        result = self.msal_app.acquire_token_by_refresh_token(
            refresh_token, scopes=settings.ms_graph_scopes_list
        )

        if "access_token" not in result:
            account.status = AccountStatus.EXPIRED
            await self.db.flush()
            raise Exception("Failed to refresh token")

        # Update stored tokens
        account.encrypted_access_token = encryption.encrypt(result["access_token"])
        if "refresh_token" in result:
            account.encrypted_refresh_token = encryption.encrypt(result["refresh_token"])
        account.token_expires_at = datetime.utcnow() + timedelta(seconds=result.get("expires_in", 3600))
        account.status = AccountStatus.ACTIVE

        await self.db.flush()
        return result["access_token"]

    async def logout(self, user_id: str) -> None:
        """Logout user by marking accounts as disconnected."""
        result = await self.db.execute(select(Account).where(Account.user_id == user_id))
        accounts = result.scalars().all()

        for account in accounts:
            account.status = AccountStatus.DISCONNECTED
            account.encrypted_access_token = ""
            account.encrypted_refresh_token = ""

        await self.db.flush()