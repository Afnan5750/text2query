# rules.py

import re
from datetime import datetime

# ----------------------
# Month mapping
# ----------------------
MONTHS = {
    "jan": "JAN", "january": "JAN",
    "feb": "FEB", "february": "FEB",
    "mar": "MAR", "march": "MAR",
    "apr": "APR", "april": "APR",
    "may": "MAY",
    "jun": "JUN", "june": "JUN",
    "jul": "JUL", "july": "JUL",
    "aug": "AUG", "august": "AUG",
    "sep": "SEP", "september": "SEP",
    "oct": "OCT", "october": "OCT",
    "nov": "NOV", "november": "NOV",
    "dec": "DEC", "december": "DEC"
}

# ----------------------
# Common phrase replacements / column mapping
# ----------------------
PHRASES = {
    "today": "CURRENT_DATE",
    "yesterday": "CURRENT_DATE - 1",
    "last month": "TRUNC(ADD_MONTHS(SYSDATE,-1),'MM')",
    "this month": "TRUNC(SYSDATE,'MM')",
    "last year": "TRUNC(ADD_MONTHS(SYSDATE,-12),'YYYY')",
    "this year": "TRUNC(SYSDATE,'YYYY')",
    
    # Column mappings
    "bill month": "B_PERIOD",
    "subdivision code": "CP22_SDIV",
    "feeder code": "CP22_FEEDER",
    "rural urban code": "CP22_RU_CODE",
    "division code": "CP22_DIV",
    "circle code": "CP22_CIR",
    "region code": "CP22_REG",
    "original subdivision code": "CP22_SDIV_ORG",
    "grid code": "CP22_GRID",
    "no of consumers": "CP22_NO_CONN",
    "sanction load": "CP22_LOAD",
    "monthly units billed": "CP22_MON_UNITS_BILLED",
    "monthly units adjusted": "CP22_MON_UNITS_ADJUSTED",
    "monthly units fed": "CP22_MON_UNITS_FED",
    "monthly units lost": "CP22_MON_UNITS_LOST",
    "subdivision share percentage": "CP22_SHARE_PER",
    "billing amount": "CP22_ASSESMENT",
    "assessment amount": "CP22_ASSESMENT",
    "spillover": "CP22_SPILL_OVER",
    "monthly payment": "CP22_PAYMENT",
    "arrear": "CP22_ARREAR",
    "domestic receivable": "CP22_RECV_DOM",
    "commercial receivable": "CP22_RECV_COM",
    "industry receivable": "CP22_RECV_IND",
    "bulk supply receivable": "CP22_RECV_B_SUPLY",
    "agriculture receivable": "CP22_RECV_AGRI",
    "street light receivable": "CP22_RECV_S_LIGHT",
    "railway traction receivable": "CP22_RECV_TRACTION",
    "others receivable": "CP22_RECV_OTHERS",
    "total receivable": "CP22_RECV_TOTAL",
    "un identified payment": "CP22_UNID_PAYMENTS",
    "progressive units billed": "CP22_PRO_UNITS_BILLED",
    "progressive units adjusted": "CP22_PRO_UNITS_ADJUSTED",
    "progressive units fed": "CP22_PRO_UNITS_FED",
    "progressive units lost": "CP22_PRO_UNITS_LOST",
    "progressive billing amount": "CP22_PRO_ASSESMENT",
    "progressive payment": "CP22_PRO_PAYMENT",
    "monthly current agency": "CP22_ASSESMENT_AGNCY",
    "progressive current agency": "CP22_PRO_ASSESMENT_AGNCY",
    "monthly agency payment": "CP22_PAYMENT_AGNCY",
    "progressive agency payment": "CP22_PRO_PAYMENT_AGNCY",
    "cc code": "CC_CODE",
    "div code": "DIVCODE",
    "creation date": "CREATED_ON",
    "modified date": "MODIFIED_ON",
    "created by": "CREATED_BY",
    "modified by": "MODIFIED_BY",
    "feeder type": "CP22_FEEDER_TYPE",
    "main feeder": "CP22_MAIN_FEEDER",
    "receivable agency": "CP22_RECV_AGENCY",
    "monthly billed net meter units": "CP22_MON_UNITS_NET",
    "monthly adjusted net meter units": "CP22_MON_UNITS_NET_ADJ",
    "progressive billed net meter units": "CP22_PRO_UNITS_NET",
    "progressive adjusted net meter units": "CP22_PRO_UNITS_NET_ADJ",
    "remarks": "REMARKS",
    "domestic receivable agency": "CP22_RECV_DOM_AGN",
    "commercial receivable agency": "CP22_RECV_COM_AGN",
    "industry receivable agency": "CP22_RECV_IND_AGN",
    "bulk supply receivable agency": "CP22_RECV_B_SUPLY_AGN",
    "agriculture receivable agency": "CP22_RECV_AGRI_AGN",
    "street light receivable agency": "CP22_RECV_S_LIGHT_AGN",
    "railway traction receivable agency": "CP22_RECV_TRACTION_AGN",
    "others receivable agency": "CP22_RECV_OTHERS_AGN",
    "total receivable agency": "CP22_SPILL_OVER_AGN",
    "monthly wheeled units": "CP22_MON_WHEELED_UNITS",
    "progressive wheeled units": "CP22_PRO_WHEELED_UNITS",
    "monthly grid import units": "CP22_MON_GRID_UNITS",
    "progressive grid import units": "CP22_PRO_GRID_UNITS"
}

# ----------------------
# Function to apply rules
# ----------------------
def apply_rules(prompt):
    """
    Convert natural language terms in prompt to SQL/Oracle-compatible formats.
    Replaces months, phrases, and formats year if present.
    """

    # 1️⃣ Replace common phrases
    for key, val in PHRASES.items():
        prompt = re.sub(rf"\b{re.escape(key)}\b", val, prompt, flags=re.IGNORECASE)

    # 2️⃣ Replace month/year patterns
    def month_repl(match):
        month = match.group('month').lower()
        year = match.group('year')
        month_oracle = MONTHS.get(month, month.upper())
        if year:
            return f"01-{month_oracle}-{year[-2:]}"
        return f"01-{month_oracle}"

    pattern = re.compile(
        r"(?P<month>\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
        r"january|february|march|april|may|june|july|august|september|october|november|december)\b)"
        r"(?:\s+(?P<year>\d{2,4}))?",
        re.IGNORECASE
    )

    prompt = pattern.sub(month_repl, prompt)
    return prompt
