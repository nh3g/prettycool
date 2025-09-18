"""Collection of all PrettyCool modules."""

from app.modules.base import (
    ActiveModule,
    ModuleExecutionError,
    ModuleMetadata,
    ModuleResult,
    PassiveModule,
)
from app.modules.censys import CensysModule
from app.modules.certspotter import CertSpotterModule
from app.modules.dnsbuffer import DNSBufferModule
from app.modules.grayhat import GrayHatWarfareModule
from app.modules.masscan import MasscanModule
from app.modules.pastebin import PasteDumpModule
from app.modules.securitytrails import SecurityTrailsModule
from app.modules.shodan import ShodanModule
from app.modules.spyse import SpyseModule
from app.modules.virustotal import VirusTotalModule
from app.modules.wayback import WaybackModule
from app.modules.whoisfreaks import WhoisFreaksModule

MODULE_REGISTRY = {
    module.metadata.name: module
    for module in (
        CensysModule,
        CertSpotterModule,
        DNSBufferModule,
        GrayHatWarfareModule,
        MasscanModule,
        PasteDumpModule,
        SecurityTrailsModule,
        ShodanModule,
        SpyseModule,
        VirusTotalModule,
        WaybackModule,
        WhoisFreaksModule,
    )
}

__all__ = [
    "MODULE_REGISTRY",
    "ModuleMetadata",
    "ModuleResult",
    "PassiveModule",
    "ActiveModule",
    "ModuleExecutionError",
]
