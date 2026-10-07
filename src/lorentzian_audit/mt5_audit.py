"""Strict safety validation for the bounded native tester launcher."""

import re
from configparser import ConfigParser
from io import StringIO


def validate_tester_config(text: str) -> None:
    config = ConfigParser(interpolation=None, strict=True)
    config.read_file(StringIO(text))
    if set(config.sections()) != {"Experts", "Tester"} or config.defaults():
        raise ValueError("Only Experts and Tester sections are permitted")
    vwap = config["Tester"].get("Expert") == r"LorentzianAudit\LorentzianVWAPAudit.ex5"
    symbol = config["Tester"].get("Symbol")
    if symbol not in {"US500", "US500_x100"}:
        raise ValueError("Research tester permits only the two explicit symbols")
    expected = {
        "Experts": {"AllowLiveTrading": "0", "AllowDllImport": "0", "Enabled": "1"},
        "Tester": {
            "Expert": r"LorentzianAudit\LorentzianVWAPAudit.ex5"
            if vwap
            else r"LorentzianAudit\LorentzianX100Audit.ex5",
            "Symbol": symbol,
            "Period": "M30",
            "UseCloud": "0",
            "UseRemote": "0",
            "UseLocal": "1",
            "Optimization": "0",
            "ShutdownTerminal": "1",
            "Visual": "0",
            "ForwardMode": "0",
            "Model": "4",
            "ReplaceReport": "0",
            "Currency": "USD",
        },
    }
    variable = {
        "executionmode",
        "fromdate",
        "todate",
        "report",
        "deposit",
        "leverage",
        "expertparameters",
    }
    for section, fields in expected.items():
        allowed = {key.lower() for key in fields} | (variable if section == "Tester" else set())
        if set(config[section]) - allowed:
            raise ValueError(f"Unsupported configuration keys in {section}")
        for key, value in fields.items():
            if config[section].get(key) != value:
                raise ValueError(f"Unsafe or unsupported value: {section}.{key}")
    parameters = config["Tester"].get("expertparameters")
    if parameters is not None and re.fullmatch(r"[a-z0-9_]+\.set", parameters) is None:
        raise ValueError("Tester parameter file must be a simple local set filename")
