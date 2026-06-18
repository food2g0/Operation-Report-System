"""Dialog components for the dashboard."""

from Client.dashboard.dialogs.detail_dialogs import (
    FundTransferHODialog,
    MotorCarDetailDialog,
    EmpenaDetailDialog
)
from Client.dashboard.dialogs.server_down_dialog import ServerDownDialog
from Client.dashboard.dialogs.transaction_detail_dialog import PalawanTransactionDetailDialog

__all__ = [
    'FundTransferHODialog',
    'MotorCarDetailDialog',
    'EmpenaDetailDialog',
    'ServerDownDialog',
    'PalawanTransactionDetailDialog'
]
