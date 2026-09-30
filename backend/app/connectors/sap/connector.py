from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

from app.connectors.base import Connector, SyncResult


class SAPConnector(Connector):
    """SAP connector using OData services (SAP Gateway/OData V2/V4)."""

    def __init__(self, base_url: str, client_id: str, client_secret: str, username: str = "", password: str = ""):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self._session = None
        self._csrf_token = None

    @property
    def name(self) -> str:
        return "sap"

    @property
    def required_scopes(self) -> list[str]:
        return []  # SAP uses basic auth or OAuth2

    async def authenticate(self, credentials: dict) -> bool:
        """Authenticate with SAP using basic auth or OAuth2."""
        import httpx

        # Update credentials if provided
        if "base_url" in credentials:
            self.base_url = credentials["base_url"].rstrip("/")
        if "client_id" in credentials:
            self.client_id = credentials["client_id"]
        if "client_secret" in credentials:
            self.client_secret = credentials["client_secret"]
        if "username" in credentials:
            self.username = credentials["username"]
        if "password" in credentials:
            self.password = credentials["password"]

        try:
            async with httpx.AsyncClient() as client:
                # Try to get CSRF token for stateful operations
                auth = None
                if self.username and self.password:
                    auth = (self.username, self.password)

                response = await client.get(
                    f"{self.base_url}/sap/opu/odata/sap/",
                    auth=auth,
                    headers={"X-CSRF-Token": "Fetch"}
                )

                if response.status_code in (200, 404):  # 404 is ok, service doc might not exist
                    self._csrf_token = response.headers.get("X-CSRF-Token")
                    self._session_cookies = response.cookies
                    return True
        except Exception:
            pass
        return False

    async def test_connection(self) -> bool:
        """Test SAP connection."""
        return await self.authenticate({})

    async def sync_incremental(
        self,
        since: datetime | None = None,
        cursor: str | None = None
    ) -> AsyncIterator[SyncResult]:
        """Sync SAP data (orders, suppliers, financial docs)."""
        result = SyncResult()

        # This is a template - actual implementation depends on SAP system
        # Common SAP OData endpoints:
        # - Purchase Orders: /sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder
        # - Suppliers: /sap/opu/odata/sap/API_BUSINESS_PARTNER/A_Supplier
        # - Financial Docs: /sap/opu/odata/sap/API_ACCOUNTING_DOCUMENT_SRV/A_AccountingDocument

        endpoints = [
            ("purchase_orders", "API_PURCHASEORDER_PROCESS_SRV", "A_PurchaseOrder"),
            ("suppliers", "API_BUSINESS_PARTNER", "A_Supplier"),
            ("accounting_docs", "API_ACCOUNTING_DOCUMENT_SRV", "A_AccountingDocument"),
        ]

        import httpx
        async with httpx.AsyncClient() as client:
            auth = (self.username, self.password) if self.username else None

            for name, service, entity in endpoints:
                try:
                    url = f"{self.base_url}/sap/opu/odata/sap/{service}/{entity}"
                    params = {"$top": 100, "$format": "json"}

                    if since:
                        # Filter by last changed date (field name varies)
                        params["$filter"] = f"LastChangeDateTime ge datetime'{since.isoformat()}'"

                    response = await client.get(url, auth=auth, params=params)

                    if response.status_code == 200:
                        data = response.json()
                        items = data.get("d", {}).get("results", [])
                        for item in items:
                            result.items_processed += 1
                            result.items_created += 1

                        yield result

                except Exception:
                    continue

    async def get_item(self, item_id: str) -> dict | None:
        """Get specific SAP document by ID."""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                auth = (self.username, self.password) if self.username else None

                # Try multiple endpoints
                endpoints = [
                    f"{self.base_url}/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder('{item_id}')",
                    f"{self.base_url}/sap/opu/odata/sap/API_BUSINESS_PARTNER/A_Supplier('{item_id}')",
                ]

                for url in endpoints:
                    response = await client.get(
                        url,
                        auth=auth,
                        params={"$format": "json"}
                    )
                    if response.status_code == 200:
                        return response.json().get("d", {})
        except Exception:
            pass
        return None

    async def search(self, query: str, limit: int = 50) -> list[dict]:
        """Search SAP documents."""
        results = []

        import httpx
        async with httpx.AsyncClient() as client:
            auth = (self.username, self.password) if self.username else None

            # Search purchase orders
            try:
                url = f"{self.base_url}/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder"
                params = {
                    "$filter": f"substringof('{query}', PurchaseOrder)",
                    "$top": limit,
                    "$format": "json"
                }
                response = await client.get(url, auth=auth, params=params)
                if response.status_code == 200:
                    items = response.json().get("d", {}).get("results", [])
                    for item in items:
                        results.append({"type": "purchase_order", **item})
            except Exception:
                pass

        return results[:limit]

    # SAP-specific operations
    async def get_purchase_orders(
        self,
        supplier_id: str | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100
    ) -> list[dict]:
        """Get purchase orders with filters."""
        import httpx
        results = []

        async with httpx.AsyncClient() as client:
            auth = (self.username, self.password) if self.username else None

            filter_parts = []
            if supplier_id:
                filter_parts.append(f"Supplier eq '{supplier_id}'")
            if status:
                filter_parts.append(f"PurchaseOrderStatus eq '{status}'")
            if date_from:
                filter_parts.append(f"OrderDate ge datetime'{date_from.isoformat()}'")
            if date_to:
                filter_parts.append(f"OrderDate le datetime'{date_to.isoformat()}'")

            params = {
                "$format": "json",
                "$top": limit,
                "$orderby": "OrderDate desc",
            }
            if filter_parts:
                params["$filter"] = " and ".join(filter_parts)

            try:
                url = f"{self.base_url}/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder"
                response = await client.get(url, auth=auth, params=params)
                if response.status_code == 200:
                    results = response.json().get("d", {}).get("results", [])
            except Exception:
                pass

        return results

    async def get_suppliers(self, search_term: str | None = None, limit: int = 100) -> list[dict]:
        """Get suppliers (business partners)."""
        import httpx
        results = []

        async with httpx.AsyncClient() as client:
            auth = (self.username, self.password) if self.username else None

            params = {"$format": "json", "$top": limit}
            if search_term:
                params["$filter"] = f"substringof('{search_term}', BusinessPartnerFullName)"

            try:
                url = f"{self.base_url}/sap/opu/odata/sap/API_BUSINESS_PARTNER/A_Supplier"
                response = await client.get(url, auth=auth, params=params)
                if response.status_code == 200:
                    results = response.json().get("d", {}).get("results", [])
            except Exception:
                pass

        return results

    async def get_accounting_documents(
        self,
        company_code: str | None = None,
        fiscal_year: str | None = None,
        limit: int = 100
    ) -> list[dict]:
        """Get accounting documents."""
        import httpx
        results = []

        async with httpx.AsyncClient() as client:
            auth = (self.username, self.password) if self.username else None

            filter_parts = []
            if company_code:
                filter_parts.append(f"CompanyCode eq '{company_code}'")
            if fiscal_year:
                filter_parts.append(f"FiscalYear eq '{fiscal_year}'")

            params = {"$format": "json", "$top": limit, "$orderby": "PostingDate desc"}
            if filter_parts:
                params["$filter"] = " and ".join(filter_parts)

            try:
                url = f"{self.base_url}/sap/opu/odata/sap/API_ACCOUNTING_DOCUMENT_SRV/A_AccountingDocument"
                response = await client.get(url, auth=auth, params=params)
                if response.status_code == 200:
                    results = response.json().get("d", {}).get("results", [])
            except Exception:
                pass

        return results

    async def create_purchase_order(self, order_data: dict) -> dict:
        """Create purchase order in SAP."""
        import httpx

        async with httpx.AsyncClient() as client:
            auth = (self.username, self.password) if self.username else None

            headers = {
                "Content-Type": "application/json",
                "X-CSRF-Token": self._csrf_token or "Fetch",
            }

            if self._session_cookies:
                client.cookies.update(self._session_cookies)

            try:
                url = f"{self.base_url}/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder"
                response = await client.post(url, auth=auth, json=order_data, headers=headers)

                if response.status_code in (201, 200):
                    return response.json().get("d", {})
                return {"error": f"Failed: {response.status_code}", "details": response.text}
            except Exception as e:
                return {"error": str(e)}
