from __future__ import annotations

from dataclasses import dataclass
import math
import re


MARKET_CSE = "CSE"
MARKET_US = "US"


@dataclass(frozen=True)
class MarketConfig:
    market: str
    label: str
    currency_code: str
    default_query: str


@dataclass(frozen=True)
class CseSecurity:
    cse_symbol: str
    company_name: str
    aliases: tuple[str, ...] = ()

    @property
    def security_code(self) -> str:
        return self.cse_symbol.split(".", 1)[0]

    @property
    def provider_symbol(self) -> str:
        return cse_display_to_provider_symbol(self.cse_symbol)


@dataclass(frozen=True)
class ResolvedSecurity:
    market: str
    market_label: str
    display_symbol: str
    provider_symbol: str
    company_name: str
    currency_code: str
    watchlist_key: str


MARKET_CONFIGS = {
    MARKET_CSE: MarketConfig(
        market=MARKET_CSE,
        label="Sri Lanka CSE",
        currency_code="LKR",
        default_query="JKH",
    ),
    MARKET_US: MarketConfig(
        market=MARKET_US,
        label="US Stocks",
        currency_code="USD",
        default_query="AAPL",
    ),
}
MARKET_OPTIONS = (MARKET_CSE, MARKET_US)


CSE_SECURITIES = (
    CseSecurity("JKH.N0000", "John Keells Holdings PLC", ("John Keells", "Keells", "JKH")),
    CseSecurity("COMB.N0000", "Commercial Bank of Ceylon PLC", ("Commercial Bank", "ComBank", "CBC", "COMB")),
    CseSecurity("HNB.N0000", "Hatton National Bank PLC", ("Hatton National Bank", "HNB")),
    CseSecurity("SAMP.N0000", "Sampath Bank PLC", ("Sampath", "Sampath Bank", "SAMP")),
    CseSecurity("NDB.N0000", "National Development Bank PLC", ("NDB", "National Development Bank")),
    CseSecurity("NTB.N0000", "Nations Trust Bank PLC", ("NTB", "Nations Trust")),
    CseSecurity("DFCC.N0000", "DFCC Bank PLC", ("DFCC", "DFCC Bank")),
    CseSecurity("DIAL.N0000", "Dialog Axiata PLC", ("Dialog", "Dialog Axiata", "DIAL")),
    CseSecurity("SLTL.N0000", "Sri Lanka Telecom PLC", ("Sri Lanka Telecom", "SLT", "SLTL")),
    CseSecurity("LOLC.N0000", "LOLC Holdings PLC", ("LOLC", "LOLC Holdings")),
    CseSecurity("CARG.N0000", "Cargills (Ceylon) PLC", ("Cargills", "Cargills Ceylon", "CARG")),
    CseSecurity("CCS.N0000", "Ceylon Cold Stores PLC", ("Ceylon Cold Stores", "Elephant House", "CCS")),
    CseSecurity("CTC.N0000", "Ceylon Tobacco Company PLC", ("Ceylon Tobacco", "CTC")),
    CseSecurity("HAYL.N0000", "Hayleys PLC", ("Hayleys", "HAYL")),
    CseSecurity("VONE.N0000", "Vallibel One PLC", ("Vallibel One", "VONE")),
    CseSecurity("SPEN.N0000", "Aitken Spence PLC", ("Aitken Spence", "SPEN")),
    CseSecurity("LIOC.N0000", "Lanka IOC PLC", ("Lanka IOC", "IOC", "LIOC")),
    CseSecurity("DIST.N0000", "Distilleries Company of Sri Lanka PLC", ("Distilleries", "DCSL", "DIST")),
    CseSecurity("RCL.N0000", "Royal Ceramics Lanka PLC", ("Royal Ceramics", "Rocell", "RCL")),
    CseSecurity("TKYO.N0000", "Tokyo Cement Company (Lanka) PLC", ("Tokyo Cement", "TKYO")),
    CseSecurity("HHL.N0000", "Hemas Holdings PLC", ("Hemas", "Hemas Holdings", "HHL")),
    CseSecurity("SUN.N0000", "Sunshine Holdings PLC", ("Sunshine", "Sunshine Holdings", "SUN")),
    CseSecurity("ACL.N0000", "ACL Cables PLC", ("ACL", "ACL Cables")),
    CseSecurity("DIPD.N0000", "Dipped Products PLC", ("Dipped Products", "DIPD")),
    CseSecurity("GRAN.N0000", "Ceylon Grain Elevators PLC", ("Ceylon Grain", "Grain Elevators", "GRAN")),
)


_CSE_SYMBOL_QUERY_PATTERN = re.compile(r"^[A-Z0-9]{1,8}(?:[.\-\s][A-Z][0-9]{4})?(?:\.CM)?$")


def market_label(market: str) -> str:
    return MARKET_CONFIGS[market].label


def _compact_text(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def cse_display_to_provider_symbol(display_symbol: str) -> str:
    normalized = normalize_cse_display_symbol(display_symbol)
    return f"{normalized.replace('.', '-', 1)}.CM"


def normalize_cse_display_symbol(query: str) -> str:
    text = query.strip().upper()
    if text.endswith(".CM"):
        text = text[:-3]
    text = text.replace("-", ".")
    text = re.sub(r"\s+", ".", text)
    if "." not in text:
        text = f"{text}.N0000"
    return text


def _looks_like_cse_symbol(query: str) -> bool:
    return bool(_CSE_SYMBOL_QUERY_PATTERN.fullmatch(query.strip().upper()))


def _find_cse_catalog_match(query: str) -> CseSecurity | None:
    normalized_query = query.strip().upper()
    compact_query = _compact_text(query)
    if not compact_query:
        return None

    for security in CSE_SECURITIES:
        if normalized_query in {security.cse_symbol, security.security_code, security.provider_symbol}:
            return security

    for security in CSE_SECURITIES:
        searchable_values = (security.company_name, security.cse_symbol, security.security_code, *security.aliases)
        compact_values = [_compact_text(value) for value in searchable_values]
        if compact_query in compact_values:
            return security
        if any(value.startswith(compact_query) for value in compact_values):
            return security
        if len(compact_query) >= 4 and any(compact_query in value for value in compact_values):
            return security

    return None


def _resolve_cse_security(query: str) -> ResolvedSecurity:
    security = _find_cse_catalog_match(query)
    if security is not None:
        display_symbol = security.cse_symbol
        company_name = security.company_name
    elif _looks_like_cse_symbol(query):
        display_symbol = normalize_cse_display_symbol(query)
        company_name = display_symbol
    else:
        raise ValueError(
            "No CSE match found. Try a company name like John Keells, a CSE code like JKH, or a full symbol like JKH.N0000."
        )

    return ResolvedSecurity(
        market=MARKET_CSE,
        market_label=MARKET_CONFIGS[MARKET_CSE].label,
        display_symbol=display_symbol,
        provider_symbol=cse_display_to_provider_symbol(display_symbol),
        company_name=company_name,
        currency_code=MARKET_CONFIGS[MARKET_CSE].currency_code,
        watchlist_key=make_watchlist_key(MARKET_CSE, display_symbol),
    )


def _resolve_us_security(query: str) -> ResolvedSecurity:
    symbol = query.strip().upper()
    if not symbol:
        raise ValueError("Please enter a US stock ticker.")

    return ResolvedSecurity(
        market=MARKET_US,
        market_label=MARKET_CONFIGS[MARKET_US].label,
        display_symbol=symbol,
        provider_symbol=symbol,
        company_name=symbol,
        currency_code=MARKET_CONFIGS[MARKET_US].currency_code,
        watchlist_key=make_watchlist_key(MARKET_US, symbol),
    )


def resolve_security(query: str, market: str) -> ResolvedSecurity:
    normalized_market = market.strip().upper()
    if normalized_market == MARKET_CSE:
        return _resolve_cse_security(query)
    if normalized_market == MARKET_US:
        return _resolve_us_security(query)
    raise ValueError(f"Unsupported market: {market}")


def make_watchlist_key(market: str, display_symbol: str) -> str:
    return f"{market.strip().upper()}:{display_symbol.strip().upper()}"


def split_watchlist_key(value: str) -> tuple[str, str]:
    text = value.strip()
    if ":" in text:
        market, query = text.split(":", 1)
        normalized_market = market.strip().upper()
        if normalized_market in MARKET_CONFIGS:
            return normalized_market, query.strip()
    return MARKET_US, text


def normalize_watchlist_key(value: str) -> str:
    market, query = split_watchlist_key(value)
    return resolve_security(query, market).watchlist_key


def resolve_watchlist_key(value: str) -> ResolvedSecurity:
    market, query = split_watchlist_key(value)
    return resolve_security(query, market)


def watchlist_label(value: str) -> str:
    try:
        security = resolve_watchlist_key(value)
    except ValueError:
        return value
    if security.company_name == security.display_symbol:
        return f"{security.market}: {security.display_symbol}"
    return f"{security.market}: {security.display_symbol} - {security.company_name}"


def format_money(value: float | int | None, currency_code: str = "USD", compact: bool = False) -> str:
    if value is None:
        return "Not available"
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "Not available"
    if not math.isfinite(numeric_value):
        return "Not available"

    currency = currency_code.upper()
    prefix = "$" if currency == "USD" else f"{currency} "
    if compact and abs(numeric_value) >= 1_000_000_000:
        return f"{prefix}{numeric_value / 1_000_000_000:.1f}B"
    if compact and abs(numeric_value) >= 1_000_000:
        return f"{prefix}{numeric_value / 1_000_000:.1f}M"
    return f"{prefix}{numeric_value:,.2f}"


def money_hover_format(currency_code: str) -> str:
    return "$%{y:,.2f}" if currency_code.upper() == "USD" else f"{currency_code.upper()} %{{y:,.2f}}"


def money_x_hover_format(currency_code: str) -> str:
    return "$%{x:,.2f}" if currency_code.upper() == "USD" else f"{currency_code.upper()} %{{x:,.2f}}"
