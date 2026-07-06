from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CSE_DATA_FILE = Path(__file__).with_name("cse_companies.json").resolve()

# Status labels for CSE companies
STATUS_LABELS = {
    0: "Trading",
    1: "Suspended",
    2: "De-listed",
    3: "Listed",
    4: "Inactive",
    5: "Unknown",
}


def _load_cse_data() -> dict[str, Any]:
    if not CSE_DATA_FILE.exists():
        return {"companies": [], "sectors": {}, "count": 0}
    try:
        data = json.loads(CSE_DATA_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "companies" in data:
            return data
        return {"companies": [], "sectors": {}, "count": 0}
    except (json.JSONDecodeError, ValueError, Exception):
        return {"companies": [], "sectors": {}, "count": 0}


class CseDirectory:
    def __init__(self, data: dict | None = None):
        if data is None:
            data = _load_cse_data()
        self._companies = data["companies"]
        self._sectors = data.get("sectors", {})
        self._build_index()

    def _build_index(self):
        self._by_symbol: dict[str, dict] = {}
        self._by_name: dict[str, dict] = {}
        self._by_security_code: dict[str, list[dict]] = {}
        self._all_symbols: list[str] = []
        self._all_names: list[str] = []
        self._all_security_codes: list[str] = []

        for company in self._companies:
            symbol = company["symbol"]
            name = company["name"]
            security_code = symbol.split(".", 1)[0]

            self._by_symbol[symbol.upper()] = company
            self._by_name[name.upper()] = company
            self._by_security_code.setdefault(security_code.upper(), []).append(company)

            self._all_symbols.append(symbol)
            self._all_names.append(name)
            self._all_security_codes.append(security_code)

    @property
    def count(self) -> int:
        return len(self._companies)

    @property
    def trading_count(self) -> int:
        return sum(1 for c in self._companies if c.get("status") == 0)

    def get_by_symbol(self, symbol: str) -> dict | None:
        return self._by_symbol.get(symbol.strip().upper())

    def get_by_security_code(self, code: str) -> dict | None:
        matches = self._by_security_code.get(code.strip().upper())
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]
        # Prefer .N0000 variant (voting shares) over .X0000 etc.
        for m in matches:
            if m["symbol"].upper().endswith(".N0000"):
                return m
        return matches[0]

    def get_by_name(self, name: str) -> dict | None:
        return self._by_name.get(name.strip().upper())

    def search(self, query: str, limit: int = 20) -> list[dict]:
        q = query.strip().upper()
        if not q:
            return []

        # Try exact matches first
        if q in self._by_symbol:
            return [self._by_symbol[q]]
        code_match = self.get_by_security_code(q)
        if code_match:
            return [code_match]

        # Split into tokens for partial matching
        q_compact = re.sub(r"[^A-Z0-9]", "", q)
        results = []

        for company in self._companies:
            name = company["name"].upper()
            symbol = company["symbol"].upper()
            security_code = symbol.split(".", 1)[0]

            name_compact = re.sub(r"[^A-Z0-9]", "", name)
            symbol_compact = re.sub(r"[^A-Z0-9]", "", symbol)

            score = 0
            if q_compact == symbol_compact:
                score = 100
            elif q_compact == security_code:
                score = 95
            elif q_compact == name_compact:
                score = 90
            elif q_compact in symbol_compact:
                score = 60
            elif q_compact in name_compact:
                score = 50
            elif any(
                q_compact in re.sub(r"[^A-Z0-9]", "", token)
                for token in name.split()
            ):
                score = 30

            # Prefer .N0000 variants when scores are equal
            if symbol.endswith(".N0000"):
                score += 0.1

            if score >= 30:
                results.append((score, company))

        results.sort(key=lambda x: -x[0])
        return [c for _, c in results][:limit]

    def autocomplete_options(self, query: str, limit: int = 20) -> list[str]:
        results = self.search(query, limit)
        options = []
        for c in results:
            symbol = c["symbol"]
            name = c["name"]
            price = c.get("price")
            status = c.get("status", 0)
            status_label = STATUS_LABELS.get(status, "Unknown")
            if price:
                options.append(f"{symbol} | {name} | LKR {price:.2f} | {status_label}")
            else:
                options.append(f"{symbol} | {name} | {status_label}")
        return options

    def parse_autocomplete_selection(self, selection: str) -> str:
        symbol = selection.split(" | ")[0] if " | " in selection else selection
        return symbol

    def get_sector_name(self, sector_id: int | str | None) -> str | None:
        if sector_id is None:
            return None
        return self._sectors.get(str(sector_id))

    def get_status_label(self, status: int) -> str:
        return STATUS_LABELS.get(status, f"Status {status}")

    def all_companies(self, only_trading: bool = True) -> list[dict]:
        if only_trading:
            return [c for c in self._companies if c.get("status") == 0]
        return self._companies

    def refresh_from_api(self):
        import requests

        r = requests.post("https://www.cse.lk/api/tradeSummary", timeout=15)
        data = r.json()
        companies = data["reqTradeSummery"]

        r2 = requests.post("https://www.cse.lk/api/allSectors", timeout=15)
        sectors_data = r2.json()

        updated = []
        for c in companies:
            symbol = c["symbol"]
            yf_symbol = symbol.replace(".N0000", "-N0000") + ".CM"
            updated.append({
                "name": c["name"],
                "symbol": symbol,
                "yfinance_symbol": yf_symbol,
                "price": c.get("price"),
                "market_cap": c.get("marketCap"),
                "status": c.get("status", 0),
                "sector": None,
                "sector_id": None,
            })

        sectors = {str(s["sectorId"]): s["name"] for s in sectors_data}

        CSE_DATA_FILE.write_text(
            json.dumps({"companies": updated, "sectors": sectors, "count": len(updated)}, indent=2),
            encoding="utf-8",
        )

        self._companies = updated
        self._sectors = sectors
        self._build_index()
        return len(updated)


def fetch_live_trade_summary() -> tuple[list[dict], dict]:
    """Fetch full tradeSummary and marketSummery from CSE API.

    Returns (companies, market_summary) where companies is the raw
    tradeSummary list (all fields: price, change, volume, marketCap, etc.)
    and market_summary is the marketSummery response dict.

    Raises RuntimeError if the CSE API is unreachable or returns an
    unexpected response.
    """
    import requests

    try:
        r = requests.post("https://www.cse.lk/api/tradeSummary", timeout=15)
        r.raise_for_status()
        data = r.json()
        companies = data.get("reqTradeSummery")
        if companies is None:
            raise ValueError("Missing 'reqTradeSummery' in CSE tradeSummary response")
    except requests.RequestException as e:
        raise RuntimeError(f"CSE API tradeSummary unavailable: {e}") from e
    except (json.JSONDecodeError, ValueError) as e:
        raise RuntimeError(f"CSE API tradeSummary response error: {e}") from e

    try:
        r2 = requests.post("https://www.cse.lk/api/marketSummery", timeout=15)
        r2.raise_for_status()
        market_summary = r2.json()
    except requests.RequestException as e:
        raise RuntimeError(f"CSE API marketSummery unavailable: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"CSE API marketSummery response error: {e}") from e

    return companies, market_summary


CSE_DIRECTORY = CseDirectory()
