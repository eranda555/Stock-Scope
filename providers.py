"""Provider abstraction for fetching stock data from different markets.

Providers encapsulate the data-fetching logic for different markets,
handling any symbol transformations needed for the underlying data source.
This keeps the app layer agnostic of provider-specific symbol formats.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import pandas as pd
import requests

if TYPE_CHECKING:
    from stock_utils import NewsSentimentResult


CSE_API_BASE = "https://www.cse.lk/api/"


class BaseProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    @abstractmethod
    def load_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """Load price history for the given ticker."""
        ...

    @abstractmethod
    def load_company_info(self, ticker: str) -> dict[str, Any]:
        """Load company info for the given ticker."""
        ...

    @abstractmethod
    def load_company_profile(self, ticker: str) -> dict[str, Any]:
        """Load company profile for the given ticker."""
        ...

    @abstractmethod
    def load_company_news(self, ticker: str, limit: int = 6) -> NewsSentimentResult:
        """Load company news for the given ticker."""
        ...


class YFinanceProvider(BaseProvider):
    """Provider that uses yfinance directly for US and other standard markets.

    The ticker is passed as-is to yfinance — no transformation needed.
    """

    def name(self) -> str:
        return "yfinance"

    def load_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        import stock_utils as su

        return su.load_price_history(ticker, period)

    def load_company_info(self, ticker: str) -> dict[str, Any]:
        import stock_utils as su

        return su.load_company_info(ticker)

    def load_company_profile(self, ticker: str) -> dict[str, Any]:
        import stock_utils as su

        return su.load_company_profile(ticker)

    def load_company_news(self, ticker: str, limit: int = 6) -> NewsSentimentResult:
        import stock_utils as su

        return su.load_company_news(ticker, limit)


class CseProvider(BaseProvider):
    """Provider for CSE (Colombo Stock Exchange, Sri Lanka) stocks.

    Uses yfinance for historical price data and the CSE public API
    for enhanced company information (real-time prices, detailed stats).
    """

    def __init__(self) -> None:
        self._session: requests.Session | None = None

    @property
    def session(self):
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def name(self) -> str:
        return "CSE API + yfinance"

    @staticmethod
    def _to_yfinance_symbol(display_symbol: str) -> str:
        symbol = display_symbol.strip().upper()
        if symbol.endswith(".CM"):
            return symbol
        if not symbol.endswith(".N0000"):
            if "." not in symbol:
                symbol = f"{symbol}.N0000"
        return symbol.replace(".", "-", 1) + ".CM"

    def _cse_api_post(self, endpoint: str, data: dict | None = None) -> dict | list:
        try:
            r = self.session.post(CSE_API_BASE + endpoint, data=data, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            return {}

    def _get_cse_symbol(self, ticker: str) -> str:
        s = ticker.strip().upper()
        if s.endswith(".CM"):
            s = s[:-3].replace("-", ".")
        if not s.endswith(".N0000"):
            if "." not in s:
                s = f"{s}.N0000"
        return s

    def load_price_history(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        import stock_utils as su

        return su.load_price_history(self._to_yfinance_symbol(ticker), period)

    def load_company_info(self, ticker: str) -> dict[str, Any]:
        import stock_utils as su

        # Start with yfinance info
        info = su.load_company_info(self._to_yfinance_symbol(ticker))

        # Enhance with CSE API data
        cse_symbol = self._get_cse_symbol(ticker)
        cse_data = self._cse_api_post("companyInfoSummery", {"symbol": cse_symbol})
        if isinstance(cse_data, dict) and "reqSymbolInfo" in cse_data:
            sym = cse_data["reqSymbolInfo"]
            info["cse_last_traded_price"] = sym.get("lastTradedPrice")
            info["cse_change"] = sym.get("change")
            info["cse_change_pct"] = sym.get("changePercentage")
            info["cse_market_cap"] = sym.get("marketCap")
            info["cse_52w_high"] = sym.get("p12HiPrice")
            info["cse_52w_low"] = sym.get("p12LowPrice")
            info["cse_volume"] = sym.get("tdyShareVolume")
            info["cse_turnover"] = sym.get("tdyTurnover")
            info["cse_previous_close"] = sym.get("previousClose")
            info["cse_open"] = sym.get("open")
            info["cse_high"] = sym.get("hiTrade")
            info["cse_low"] = sym.get("lowTrade")
            info["cse_beta"] = None
            if "reqSymbolBetaInfo" in cse_data:
                beta = cse_data["reqSymbolBetaInfo"]
                info["cse_beta"] = beta.get("betaValueSPSL")

        return info

    def load_company_profile(self, ticker: str) -> dict[str, Any]:
        import stock_utils as su

        profile = su.load_company_profile(self._to_yfinance_symbol(ticker))

        # Enhance with CSE API data
        cse_symbol = self._get_cse_symbol(ticker)
        cse_data = self._cse_api_post("companyInfoSummery", {"symbol": cse_symbol})
        if isinstance(cse_data, dict) and "reqSymbolInfo" in cse_data:
            sym = cse_data["reqSymbolInfo"]
            profile["name"] = profile.get("name") or sym.get("name", ticker)
            profile["marketCap"] = profile.get("marketCap") or sym.get("marketCap")
            profile["sector"] = profile.get("sector")
            profile["industry"] = profile.get("industry")
            profile["country"] = profile.get("country", "Sri Lanka")

        return profile

    def load_company_news(self, ticker: str, limit: int = 6) -> NewsSentimentResult:
        import stock_utils as su

        return su.load_company_news(self._to_yfinance_symbol(ticker), limit)


# ---------------------------------------------------------------------------
# Provider registry (singletons, lazily created)
# ---------------------------------------------------------------------------
_providers: dict[str, BaseProvider] = {}


def get_provider(market: str) -> BaseProvider:
    """Return the appropriate data provider for *market*.

    Parameters
    ----------
    market : str
        Market identifier (``"CSE"`` or ``"US"``).

    Returns
    -------
    BaseProvider
        A cached provider instance suitable for the market.
    """
    from markets import MARKET_CSE

    market_key = market.strip().upper()
    if market_key == MARKET_CSE:
        if "cse" not in _providers:
            _providers["cse"] = CseProvider()
        return _providers["cse"]

    # Default to YFinanceProvider for US and any other market.
    if "yf" not in _providers:
        _providers["yf"] = YFinanceProvider()
    return _providers["yf"]
