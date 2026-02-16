# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Standard Action Codes for Archival & Backup Operations.
Aligned with ISO/IEC 27040:2024 and ISO 14721 (OAIS).
"""

import json
from enum import IntEnum
from pathlib import Path
from typing import Dict, Any

def _load_lut() -> Dict[str, Any]:
    """Load the ISO standard compliant LUT from disk."""
    lut_path = Path(__file__).parent / "lut.json"
    if not lut_path.exists():
        return {"codes": []}
    with open(lut_path, "r", encoding="utf-8") as f:
        return json.load(f)

_LUT_DATA = _load_lut()

# Dynamically create the IntEnum based on JSON data
_enum_members = {
    item['mnemonic']: item['code'] 
    for item in _LUT_DATA.get('codes', [])
}

# Refocused aliases for Archival and Backup mission
_aliases = {
    "IPC_START": "FAU_GEN_START",
    "IPC_REQ_RECEIVED": "FAU_SAR_REQ",
    "ARCHIVE_SIP": "OAIS_SIP_INGEST",
    "ARCHIVE_AIP": "OAIS_AIP_STORE",
    "DEDUP_FP": "DEDUP_FP_GEN",
    "DEDUP_REF": "DEDUP_REF_ADD",
    "DEDUP_GC": "DEDUP_RECLAIM",
    "BKP_VERIFY": "BKP_VERIFY_OK",
    "BKP_RESTORE": "BKP_RESTORE_FAIL",
    "BKP_FAULT": "BKP_MEDIA_FAULT",
    "PRESERV_CHECK": "PRESERV_FIXITY",
    "ERR_EXEC_FAILED": "FPT_FLS_FAIL",
    "HASHING_OP": "FDP_DAU_HASH",
    "TOOL_INIT": "FIA_UAU_INIT",
    "TOOL_LOAD": "FIA_UAU_LOAD",
    "TOOL_SHUTDOWN": "FIA_UAU_SHUTDOWN",
    "ERR_INTERNAL": "FPT_STM_ERR",
    "DB_OP": "FDP_ETC_DB",
    "ARCHIVE_OP": "FDP_DAU_ARCH",
    "ERR_TOOL_NOT_FOUND": "FPT_FLS_FAIL",
    "ERR_METHOD_NOT_FOUND": "FPT_FLS_FAIL",
    "ERR_INVALID_REQUEST": "FPT_FLS_FAIL",
    "ERR_INVALID_JSON": "FPT_FLS_FAIL",
    "RATE_LIMIT_HIT": "FPT_FLS_FAIL",
    "SECURITY_RISK_FLAGGED": "FPT_FLS_FAIL",
    "HOT_RELOAD_START": "FMT_MOF_RELOAD",
    "HOT_RELOAD_STOP": "FMT_MOF_RELOAD",
    "HOT_RELOAD_DETECT": "FMT_MOF_RELOAD",
    "HOT_RELOAD_SUCCESS": "FMT_MOF_RELOAD",
    "ML_LOAD": "ML_MOD_LOAD",
    "ML_INF": "ML_INF_START",
    "GPU_OP": "FRU_RSA_GPU",
    # Accessibility-specific codes for ISO compliance
    "ACC_SCREEN_READER_INIT": "ACC_SCR_RD_INIT",
    "ACC_SCREEN_READER_AVAIL": "ACC_SCR_RD_AVAIL",
    "ACC_SCREEN_READER_UNAVAIL": "ACC_SCR_RD_UNAVAIL",
    "ACC_BRAILLE_INIT": "ACC_BRL_INIT",
    "ACC_BRAILLE_AVAIL": "ACC_BRL_AVAIL",
    "ACC_BRAILLE_UNAVAIL": "ACC_BRL_UNAVAIL",
    "ACC_OUTPUT_SENT": "ACC_OUT_SENT",
    "ACC_OUTPUT_FAILED": "ACC_OUT_FAIL",
    "ACC_FEATURE_ENABLED": "ACC_FEAT_ENAB",
    "ACC_FEATURE_DISABLED": "ACC_FEAT_DISAB",
    "ACC_LIB_LOAD_SUCCESS": "ACC_LIB_LOAD_OK",
    "ACC_LIB_LOAD_FAIL": "ACC_LIB_LOAD_FAIL",
    "ACC_CONSOLE_FALLBACK": "ACC_CONS_FALL",
    "ACC_ISO_COMPLIANT": "ACC_ISO_CMP"
}

for alias, target in _aliases.items():
    if target in _enum_members:
        _enum_members[alias] = _enum_members[target]

ActionCode = IntEnum('ActionCode', _enum_members)

def _get_lut(cls) -> Dict[str, Any]:
    return _LUT_DATA

def _get_description(cls, code: int) -> str:
    for item in _LUT_DATA.get("codes", []):
        if item["code"] == code:
            return item["description"]
    return "Unknown Action"

def _get_category(cls, code: int) -> str:
    """Get the ISO tool category for a specific code."""
    for item in _LUT_DATA.get("codes", []):
        if item["code"] == code:
            iso_class = item.get("iso_class")
            # Map ISO Class to Category Header
            mapping = {
                "OAIS": "ARCHIVE",
                "FDP": "PROTECTION",
                "FCS": "CRYPTO",
                "ML": "AI_ML",
                "FRU": "HARDWARE",
                "FCO": "NETWORK"
            }
            return mapping.get(iso_class, "GENERAL")
    return "GENERAL"

def _to_jsonrpc_code(cls, internal_code: int) -> int:
    """Map internal ISO codes to JSON-RPC 2.0 standard error codes."""
    if internal_code >= 530000: return -32603 # Backup/Media fault
    if internal_code >= 500000: return -32000 # Engine failure
    return -32099

setattr(ActionCode, 'get_lut', classmethod(_get_lut))
setattr(ActionCode, 'get_description', classmethod(_get_description))
setattr(ActionCode, 'get_category', classmethod(_get_category))
setattr(ActionCode, 'to_jsonrpc_code', classmethod(_to_jsonrpc_code))

# Mapping of method names to action codes for risk assessment
SENSITIVE_METHODS = {
    'extract_archive': getattr(ActionCode, 'OAIS_SIP_INGEST', 120000),
    'delete_file': getattr(ActionCode, 'DEDUP_RECLAIM', 250002),
}

# Risk categorization
RISK_LEVELS = {
    getattr(ActionCode, 'FPT_FLS_FAIL', 500000): "CRITICAL",
    getattr(ActionCode, 'BKP_RESTORE_FAIL', 530001): "CRITICAL",
    getattr(ActionCode, 'BKP_MEDIA_FAULT', 530002): "HIGH",
}
