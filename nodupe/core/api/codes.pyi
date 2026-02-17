# Type stub for dynamically-created ActionCode enum
# This tells static type checkers about the enum members
#
# SPDX-License-Identifier: Apache-2.0

from enum import IntEnum
from typing import Any

class ActionCode(IntEnum):
    """ISO-standard action codes for archival and backup operations."""

    # Core FAU codes (100xxx)
    FAU_GEN_START: int
    FAU_GEN_STOP: int
    FAU_SAR_REQ: int
    FAU_SAR_RES: int

    # FDP codes (200xxx)
    FDP_DAU_HASH: int
    FDP_ETC_DB: int

    # DDP codes (250xxx)
    DEDUP_RECLAIM: int

    # FIA codes (300xxx)
    FIA_UAU_LOAD: int
    FIA_UAU_INIT: int
    FIA_UAU_SHUTDOWN: int

    # FMT codes (400xxx)
    FMT_MOF_RELOAD: int

    # FPT codes - general errors (500xxx)
    FPT_FLS_FAIL: int
    FPT_STM_ERR: int
    FPT_SEP_DENIED: int

    # FPT codes - custom error codes (5000xx)
    ERR_INTERNAL: int
    RATE_LIMIT_HIT: int
    ERR_INVALID_JSON: int
    ERR_INVALID_REQUEST: int
    ERR_TOOL_NOT_FOUND: int
    ERR_METHOD_NOT_FOUND: int
    ERR_EXEC_FAILED: int
    SECURITY_RISK_FLAGGED: int

    # OAIS codes (120xxx)
    OAIS_SIP_INGEST: int
    OAIS_AIP_STORE: int

    # ACC codes (600xxx)
    ACC_SCR_RD_INIT: int
    ACC_SCR_RD_AVAIL: int
    ACC_SCR_RD_UNAVAIL: int
    ACC_BRL_INIT: int
    ACC_BRL_AVAIL: int
    ACC_BRL_UNAVAIL: int
    ACC_OUT_SENT: int
    ACC_OUT_FAIL: int
    ACC_FEAT_ENAB: int
    ACC_FEAT_DISAB: int
    ACC_LIB_LOAD_OK: int
    ACC_LIB_LOAD_FAIL: int
    ACC_CONS_FALL: int
    ACC_ISO_CMP: int

    # Aliases
    IPC_START: int
    IPC_REQ_RECEIVED: int
    ARCHIVE_SIP: int
    ARCHIVE_AIP: int
    DEDUP_FP: int
    DEDUP_REF: int
    DEDUP_GC: int
    BKP_VERIFY: int
    BKP_RESTORE: int
    BKP_FAULT: int
    PRESERV_CHECK: int
    HASHING_OP: int
    TOOL_INIT: int
    TOOL_LOAD: int
    TOOL_SHUTDOWN: int
    DB_OP: int
    ARCHIVE_OP: int
    HOT_RELOAD_START: int
    HOT_RELOAD_STOP: int
    HOT_RELOAD_DETECT: int
    HOT_RELOAD_SUCCESS: int
    ML_LOAD: int
    ML_INF: int
    GPU_OP: int
    ACC_SCREEN_READER_INIT: int
    ACC_SCREEN_READER_AVAIL: int
    ACC_SCREEN_READER_UNAVAIL: int
    ACC_BRAILLE_INIT: int
    ACC_BRAILLE_AVAIL: int
    ACC_BRAILLE_UNAVAIL: int
    ACC_OUTPUT_SENT: int
    ACC_OUTPUT_FAILED: int
    ACC_FEATURE_ENABLED: int
    ACC_FEATURE_DISABLED: int
    ACC_LIB_LOAD_SUCCESS: int
    ACC_CONSOLE_FALLBACK: int
    ACC_ISO_COMPLIANT: int

    # Class methods added via setattr in codes.py
    @classmethod
    def get_lut(cls) -> dict[str, Any]:
        """Return the lookup table (LUT) containing all action codes and metadata."""

    @classmethod
    def get_description(cls, code: int) -> str:
        """Get the human-readable description for an action code."""

    @classmethod
    def get_category(cls, code: int) -> str:
        """Get the ISO category for a specific action code."""

    @classmethod
    def to_jsonrpc_code(cls, internal_code: int) -> int:
        """Convert an internal ISO code to a JSON-RPC 2.0 standard error code."""

# Module-level variables
SENSITIVE_METHODS: dict[str, int]
RISK_LEVELS: dict[int, str]
