# Dashboard Module

Organized structure for the ClientDashboard and all related components.

## Structure

```
dashboard/
├── main.py                    # ClientDashboard core class
├── dialogs/                   # Dialog classes
│   ├── __init__.py
│   ├── detail_dialogs.py     # Fund Transfer, Motor Car, Empeno dialogs
│   ├── salary_dialog.py      # PC Salary breakdown
│   └── jewelry_dialog.py     # Jewelry operations
├── managers/                  # Business logic managers
│   ├── __init__.py
│   ├── balance_manager.py    # Balance calculations and entry management
│   ├── palawan_manager.py    # Palawan data handling
│   └── offline_manager.py    # Offline mode support
├── builders/                  # UI component builders
│   ├── __init__.py
│   └── ui_builders.py        # Reusable UI component builders
├── handlers/                  # Event and data handlers
│   ├── __init__.py
│   ├── post_handler.py       # Report posting workflow
│   ├── signal_manager.py     # Qt signal management
│   └── validation_handler.py # Data validation
└── utils/                     # Utility functions
    ├── __init__.py
    └── formatting.py         # Formatting helpers
```

## Imports

### Old way (still works - backward compatible):
```python
from Client.client_dashboard import ClientDashboard
```

### New way (recommended):
```python
from Client.dashboard import ClientDashboard
# or
from Client.dashboard.main import ClientDashboard
```

## Refactoring Status

- ✅ Folder structure created
- ✅ main.py moved to dashboard/
- ✅ Backward compatibility maintained
- ⏳ Extract dialogs to dialogs/ folder
- ⏳ Extract managers to managers/ folder
- ⏳ Extract builders to builders/ folder
- ⏳ Extract handlers to handlers/ folder

## Next Steps

1. Extract FundTransferHODialog, MotorCarDetailDialog, EmpenaDetailDialog → dialogs/
2. Extract balance calculation logic → managers/balance_manager.py
3. Extract palawan logic → managers/palawan_manager.py
4. Extract UI builders → builders/ui_builders.py
5. Extract posting logic → handlers/post_handler.py
6. Extract signal connections → handlers/signal_manager.py
7. Add unit tests for each component

## Benefits

- Clear separation of concerns
- Easier to find and modify code
- Better testability
- Scalable as features grow
- Reduced complexity per file
