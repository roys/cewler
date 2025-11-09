from dataclasses import dataclass, field
from typing import Dict


@dataclass
class CewlerConfig:
    """Configuration for cewler crawling session"""
    url: str
    user_agent: str
    depth: int
    rate: float # Requests per second
    subdomain_strategy: str
    min_word_length: int
    include_js: bool
    include_css: bool
    include_pdf: bool
    lowercase: bool
    without_numbers: bool
    verbose: bool
    output: str = None
    output_emails: str = None
    output_urls: str = None
    stream: bool = False
    custom_headers: Dict[str, str] = field(default_factory=dict)
