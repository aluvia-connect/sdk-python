"""
BlockDetection - Website block detection with weighted scoring

Port of the Node SDK BlockDetection class to Python.
Detects website blocks, CAPTCHAs, and WAF challenges using a weighted scoring system.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, Optional, Set, List
from urllib.parse import urlparse

from .logger import Logger


# Type aliases
DetectionBlockStatus = str  # "blocked" | "suspected" | "clear"


@dataclass
class DetectionSignal:
    """A single detection signal with weight"""
    name: str
    weight: float
    details: str
    source: str  # "fast" | "full"


@dataclass
class RedirectHop:
    """A single hop in a redirect chain"""
    url: str
    status_code: int


@dataclass
class BlockDetectionResult:
    """Result of block detection analysis"""
    url: str
    hostname: str
    block_status: DetectionBlockStatus
    score: float
    signals: List[DetectionSignal]
    pass_type: str  # "fast" | "full"
    persistent_block: bool
    redirect_chain: List[RedirectHop]


@dataclass
class BlockDetectionConfig:
    """Configuration for block detection"""
    enabled: bool = True
    challenge_selectors: Optional[List[str]] = None
    extra_keywords: Optional[List[str]] = None
    extra_status_codes: Optional[List[int]] = None
    network_idle_timeout_ms: int = 3000
    auto_unblock: bool = False
    auto_unblock_on_suspected: bool = False
    on_detection: Optional[Callable[[BlockDetectionResult, Any], Awaitable[None]]] = None


# Default challenge selectors
DEFAULT_CHALLENGE_SELECTORS = [
    "#challenge-form",
    "#challenge-running",
    ".cf-browser-verification",
    'iframe[src*="recaptcha"]',
    ".g-recaptcha",
    "#px-captcha",
    'iframe[src*="hcaptcha"]',
    ".h-captcha",
]

# Detection keywords
TITLE_KEYWORDS = [
    "access denied",
    "blocked",
    "forbidden",
    "security check",
    "attention required",
    "just a moment",
]

STRONG_TEXT_KEYWORDS = [
    "captcha",
    "access denied",
    "verify you are human",
    "bot detection",
]

WEAK_TEXT_KEYWORDS = [
    "blocked",
    "forbidden",
    "cloudflare",
    "please verify",
    "unusual activity",
]

CHALLENGE_DOMAIN_PATTERNS = [
    "/cdn-cgi/challenge-platform/",
    "challenges.cloudflare.com",
    "geo.captcha-delivery.com",
]


class BlockDetection:
    """
    BlockDetection handles detection of website blocks, CAPTCHAs, and WAF challenges
    using a weighted scoring system across multiple signal types.
    """

    def __init__(self, config: BlockDetectionConfig, logger: Logger):
        self.logger = logger
        self.config = config

        # Use defaults if not provided
        if self.config.challenge_selectors is None:
            self.config.challenge_selectors = DEFAULT_CHALLENGE_SELECTORS
        if self.config.extra_keywords is None:
            self.config.extra_keywords = []
        if self.config.extra_status_codes is None:
            self.config.extra_status_codes = []

        # Persistent block tracking
        self.retried_urls: Set[str] = set()
        self.persistent_hostnames: Set[str] = set()

        # Pre-computed lookup structures
        self.status_code_set = {403, 429, *self.config.extra_status_codes}
        self.all_title_keywords = [*TITLE_KEYWORDS, *self.config.extra_keywords]
        
        # Pre-compile weak text regexes for performance
        self.weak_text_patterns = [
            {
                "keyword": keyword,
                "regex": re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            }
            for keyword in WEAK_TEXT_KEYWORDS
        ]

    def get_network_idle_timeout_ms(self) -> int:
        """Get the network idle timeout in milliseconds"""
        return self.config.network_idle_timeout_ms

    def is_enabled(self) -> bool:
        """Check if block detection is enabled"""
        return self.config.enabled

    def get_on_detection(self) -> Optional[Callable[[BlockDetectionResult, Any], Awaitable[None]]]:
        """Get the onDetection callback"""
        return self.config.on_detection

    def is_auto_unblock(self) -> bool:
        """Check if auto-unblock is enabled"""
        return self.config.auto_unblock

    def is_auto_unblock_on_suspected(self) -> bool:
        """Check if auto-unblock on suspected blocks is enabled"""
        return self.config.auto_unblock_on_suspected

    # --- Scoring Engine ---

    def _compute_score(self, signals: List[DetectionSignal]) -> tuple[float, DetectionBlockStatus]:
        """Compute weighted score from signals"""
        if not signals:
            return 0.0, "clear"
        
        # Combine weights probabilistically: 1 - product(1 - weight_i)
        product = 1.0
        for signal in signals:
            product *= (1 - signal.weight)
        
        score = 1 - product
        
        # Determine block status from score
        if score >= 0.7:
            block_status = "blocked"
        elif score >= 0.4:
            block_status = "suspected"
        else:
            block_status = "clear"
        
        return score, block_status

    # --- Fast-pass Signal Detectors ---

    def _detect_http_status(self, response: Any) -> Optional[DetectionSignal]:
        """Detect block signals from HTTP status code"""
        try:
            if not response:
                return None
            
            status = response.status
            if status == 0:
                return None
            
            if status in self.status_code_set:
                return DetectionSignal(
                    name=f"http_status_{status}",
                    weight=0.85,
                    details=f"HTTP {status} response",
                    source="fast"
                )
            
            if status == 503:
                return DetectionSignal(
                    name="http_status_503",
                    weight=0.6,
                    details="HTTP 503 response",
                    source="fast"
                )
        except Exception as err:
            self.logger.debug(f"Detection check failed: {err}")
        
        return None

    def _detect_response_headers(self, response: Any) -> List[DetectionSignal]:
        """Detect block signals from response headers"""
        signals = []
        
        try:
            if not response:
                return signals
            
            headers = response.headers
            
            # Check cf-mitigated header
            cf_mitigated = headers.get("cf-mitigated", "")
            if cf_mitigated and "challenge" in cf_mitigated.lower():
                signals.append(DetectionSignal(
                    name="waf_header_cf_mitigated",
                    weight=0.9,
                    details=f"cf-mitigated: {cf_mitigated}",
                    source="fast"
                ))
            
            # Check server header for Cloudflare
            server = headers.get("server", "")
            if server and "cloudflare" in server.lower():
                signals.append(DetectionSignal(
                    name="waf_header_cloudflare",
                    weight=0.1,
                    details=f"server: {server}",
                    source="fast"
                ))
        except Exception as err:
            self.logger.debug(f"Detection check failed: {err}")
        
        return signals

    # --- Full-pass Signal Detectors ---

    async def _detect_title_keywords(self, page: Any) -> Optional[DetectionSignal]:
        """Detect block signals from page title"""
        try:
            title = (await page.title()).lower()
            for keyword in self.all_title_keywords:
                if keyword.lower() in title:
                    return DetectionSignal(
                        name="title_keyword",
                        weight=0.8,
                        details=f'Title contains "{keyword}"',
                        source="full"
                    )
        except Exception as err:
            self.logger.debug(f"Detection check failed: {err}")
        
        return None

    async def _detect_challenge_selectors(self, page: Any) -> Optional[DetectionSignal]:
        """Detect challenge selectors on the page"""
        try:
            selectors = self.config.challenge_selectors
            found = await page.evaluate("""
                (selectors) => {
                    for (const sel of selectors) {
                        if (document.querySelector(sel)) return sel;
                    }
                    return null;
                }
            """, selectors)
            
            if found:
                return DetectionSignal(
                    name="challenge_selector",
                    weight=0.8,
                    details=f"Challenge selector found: {found}",
                    source="full"
                )
        except Exception as err:
            self.logger.debug(f"Detection check failed: {err}")
        
        return None

    async def _detect_visible_text(self, page: Any, use_inner_text: bool = False) -> List[DetectionSignal]:
        """Detect block signals from visible text on the page"""
        signals = []
        
        try:
            if use_inner_text:
                text = await page.evaluate("() => document.body?.innerText ?? ''")
            else:
                text = await page.evaluate("() => document.body?.textContent ?? ''")
            
            text_lower = text.lower()
            text_length = len(text)
            
            # Short text signal
            if text_length < 50:
                signals.append(DetectionSignal(
                    name="visible_text_short",
                    weight=0.2,
                    details=f"Visible text very short ({text_length} chars)",
                    source="full"
                ))
            
            # Strong keywords on short pages
            if text_length < 500:
                all_strong = [*STRONG_TEXT_KEYWORDS, *self.config.extra_keywords]
                for keyword in all_strong:
                    if keyword.lower() in text_lower:
                        signals.append(DetectionSignal(
                            name="visible_text_keyword_strong",
                            weight=0.6,
                            details=f'Strong keyword "{keyword}" on short page',
                            source="full"
                        ))
                        break
            
            # Weak keywords with word boundary
            for pattern_info in self.weak_text_patterns:
                if pattern_info["regex"].search(text):
                    signals.append(DetectionSignal(
                        name="visible_text_keyword_weak",
                        weight=0.15,
                        details=f'Weak keyword "{pattern_info["keyword"]}" found with word boundary',
                        source="full"
                    ))
                    break
        except Exception as err:
            self.logger.debug(f"Detection check failed: {err}")
        
        return signals

    async def _detect_text_to_html_ratio(self, page: Any) -> Optional[DetectionSignal]:
        """Detect low text-to-HTML ratio"""
        try:
            result = await page.evaluate("""
                () => {
                    const html = document.documentElement?.outerHTML ?? '';
                    const text = document.body?.textContent ?? '';
                    return { htmlLength: html.length, textLength: text.length };
                }
            """)
            
            html_length = result["htmlLength"]
            text_length = result["textLength"]
            
            if html_length >= 1000 and text_length / html_length < 0.03:
                return DetectionSignal(
                    name="low_text_ratio",
                    weight=0.2,
                    details=f"Low text/HTML ratio: {text_length}/{html_length}",
                    source="full"
                )
        except Exception as err:
            self.logger.debug(f"Detection check failed: {err}")
        
        return None

    def _detect_redirect_chain(self, response: Any) -> tuple[List[DetectionSignal], List[RedirectHop]]:
        """Detect block signals from redirect chain"""
        chain: List[RedirectHop] = []
        signals: List[DetectionSignal] = []
        
        try:
            if not response:
                return signals, chain
            
            # Walk redirect chain backwards using Playwright's redirectedFrom
            req = response.request
            hops = []
            
            while req:
                redirected_from = getattr(req, 'redirected_from', None)
                if not redirected_from:
                    break
                
                # In Playwright Python, Request.response() is async; avoid
                # calling it here and just record the redirect URL.
                hops.append(RedirectHop(
                    url=redirected_from.url,
                    status_code=0,
                ))
                
                req = redirected_from
            
            # Reverse to get chronological order
            hops.reverse()
            chain.extend(hops)
            
            # Check if any hop URL matches challenge domain patterns
            for hop in chain:
                for pattern in CHALLENGE_DOMAIN_PATTERNS:
                    if pattern in hop.url:
                        signals.append(DetectionSignal(
                            name="redirect_to_challenge",
                            weight=0.7,
                            details=f"Redirect through challenge domain: {hop.url}",
                            source="full"
                        ))
                        return signals, chain
            
            # Also check final response URL
            final_url = response.url
            for pattern in CHALLENGE_DOMAIN_PATTERNS:
                if pattern in final_url:
                    signals.append(DetectionSignal(
                        name="redirect_to_challenge",
                        weight=0.7,
                        details=f"Final URL is challenge domain: {final_url}",
                        source="full"
                    ))
                    break
        except Exception as err:
            self.logger.debug(f"Detection check failed: {err}")
        
        return signals, chain

    async def _detect_meta_refresh(self, page: Any) -> Optional[DetectionSignal]:
        """Detect meta refresh to challenge pages"""
        try:
            refresh_url = await page.evaluate("""
                () => {
                    const meta = document.querySelector('meta[http-equiv="refresh"]');
                    if (!meta) return null;
                    const content = meta.getAttribute('content') ?? '';
                    const match = content.match(/url\\s*=\\s*(.+)/i);
                    return match ? match[1].trim() : null;
                }
            """)
            
            if refresh_url:
                for pattern in CHALLENGE_DOMAIN_PATTERNS:
                    if pattern in refresh_url:
                        return DetectionSignal(
                            name="meta_refresh_challenge",
                            weight=0.65,
                            details=f"Meta refresh to challenge URL: {refresh_url}",
                            source="full"
                        )
        except Exception as err:
            self.logger.debug(f"Detection check failed: {err}")
        
        return None

    # --- Two-Pass Analysis API ---

    async def analyze_fast(self, page: Any, response: Any) -> BlockDetectionResult:
        """
        Fast pass - runs at domcontentloaded. Only HTTP status + response headers.
        If score >= 0.9, caller should trigger remediation immediately.
        """
        url = page.url
        hostname = self._extract_hostname(url)
        
        if not self.config.enabled:
            return self._make_result(url, hostname, [], "fast", [])
        
        signals: List[DetectionSignal] = []
        
        # Detect HTTP status
        status_signal = self._detect_http_status(response)
        if status_signal:
            signals.append(status_signal)
        
        # Detect response headers
        header_signals = self._detect_response_headers(response)
        signals.extend(header_signals)
        
        result = self._make_result(url, hostname, signals, "fast", [])
        self._log_result(result)
        return result

    async def _run_content_detectors(self, page: Any) -> List[DetectionSignal]:
        """Run all content-based detectors in parallel"""
        import asyncio
        
        results = await asyncio.gather(
            self._detect_title_keywords(page),
            self._detect_challenge_selectors(page),
            self._detect_visible_text(page, False),
            self._detect_text_to_html_ratio(page),
            self._detect_meta_refresh(page),
            return_exceptions=True
        )
        
        signals: List[DetectionSignal] = []
        
        # Unpack results (handle both signals and lists of signals)
        for result in results:
            if isinstance(result, Exception):
                self.logger.debug(f"Content detector failed: {result}")
            elif isinstance(result, list):
                signals.extend(result)
            elif result is not None:
                signals.append(result)
        
        return signals

    async def analyze_full(
        self, 
        page: Any, 
        response: Any, 
        fast_result: Optional[BlockDetectionResult] = None
    ) -> BlockDetectionResult:
        """
        Full pass - runs after networkidle. Runs all detectors and merges with fast pass.
        """
        url = page.url
        hostname = self._extract_hostname(url)
        
        if not self.config.enabled:
            return self._make_result(url, hostname, [], "full", [])
        
        # Start with fast-pass signals
        signals: List[DetectionSignal] = []
        if fast_result:
            signals.extend(fast_result.signals)
        
        # If no fast pass was done and we have a response, run fast detectors
        if not fast_result and response:
            status_signal = self._detect_http_status(response)
            if status_signal:
                signals.append(status_signal)
            
            header_signals = self._detect_response_headers(response)
            signals.extend(header_signals)
        
        # Run content-based detectors
        content_signals = await self._run_content_detectors(page)
        signals.extend(content_signals)
        
        # Detect redirect chain
        redirect_signals, chain = self._detect_redirect_chain(response)
        signals.extend(redirect_signals)
        
        return await self._re_evaluate_if_suspected(page, url, hostname, signals, chain)

    async def analyze_spa(self, page: Any) -> BlockDetectionResult:
        """
        SPA navigation analysis - content-based detectors only, no HTTP signals.
        """
        url = page.url
        hostname = self._extract_hostname(url)
        
        if not self.config.enabled:
            return self._make_result(url, hostname, [], "full", [])
        
        signals = await self._run_content_detectors(page)
        return await self._re_evaluate_if_suspected(page, url, hostname, signals, [])

    async def _re_evaluate_if_suspected(
        self, 
        page: Any, 
        url: str, 
        hostname: str, 
        signals: List[DetectionSignal], 
        redirect_chain: List[RedirectHop]
    ) -> BlockDetectionResult:
        """Re-evaluate with innerText if score is in suspected range"""
        score, block_status = self._compute_score(signals)
        
        if 0.4 <= score < 0.7:
            # Re-evaluate with innerText instead of textContent
            non_text_signals = [s for s in signals if not s.name.startswith("visible_text_")]
            inner_text_signals = await self._detect_visible_text(page, True)
            non_text_signals.extend(inner_text_signals)
            
            result = self._make_result(url, hostname, non_text_signals, "full", redirect_chain)
            self._log_result(result)
            return result
        
        result = self._make_result(url, hostname, signals, "full", redirect_chain)
        self._log_result(result)
        return result

    # --- Utility Methods ---

    def _make_result(
        self, 
        url: str, 
        hostname: str, 
        signals: List[DetectionSignal], 
        pass_type: str, 
        redirect_chain: List[RedirectHop]
    ) -> BlockDetectionResult:
        """Create a detection result from signals"""
        score, block_status = self._compute_score(signals)
        return BlockDetectionResult(
            url=url,
            hostname=hostname,
            block_status=block_status,
            score=score,
            signals=signals,
            pass_type=pass_type,
            persistent_block=False,
            redirect_chain=redirect_chain
        )

    def _log_result(self, result: BlockDetectionResult) -> None:
        """Log detection result for debugging"""
        if not self.logger.is_debug:
            return
        
        self.logger.debug(
            f"Detection result: url={result.url}, blockStatus={result.block_status}, "
            f"score={result.score:.2f}, signals={len(result.signals)}, pass={result.pass_type}"
        )

    def _extract_hostname(self, url: str) -> str:
        """Extract hostname from URL"""
        try:
            parsed = urlparse(url)
            return parsed.hostname or url
        except Exception:
            return url
