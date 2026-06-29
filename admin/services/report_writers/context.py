from dataclasses import dataclass, field


@dataclass
class ReportContext:
    db:            object
    brand_label:   str
    is_brand_a:    bool
    filter_type:   str       # "corporation" | "os"
    filter_value:  str
    filter_label:  str       # "Corporation" | "Group"
    selected_date: str       # "YYYY-MM-DD"
    reg_filter:    str       # "registered" | "not_registered" | "all"
    daily_table:   str
    debit_fields:  dict
    credit_fields: dict
    bank_accounts: list
    col_cache:     dict = field(default_factory=dict)
