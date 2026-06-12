"""Export handler - manages report export to Excel."""

import logging
import os
import datetime

logger = logging.getLogger(__name__)


class ExportHandler:
    """Handles report export to Excel files."""

    def __init__(self, branch, corporation):
        """Initialize export handler.

        Args:
            branch: Branch name
            corporation: Corporation name
        """
        self.branch = branch
        self.corporation = corporation

    def validate_file_path(self, file_path):
        """Validate file path for security (prevent directory traversal).

        Args:
            file_path: Path to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        file_path = os.path.abspath(file_path)
        home_dir = os.path.expanduser("~")
        documents_dir = os.path.join(home_dir, "Documents")

        if not (file_path.startswith(documents_dir) or file_path.startswith(home_dir)):
            logger.error(f"Invalid file path: {file_path}")
            return False, "File must be saved in Documents or home directory"

        return True, ""

    def build_workbook(self, wb, data_dict, selected_date, user_email, brands_to_export):
        """Build Excel workbook with report data.

        Args:
            wb: Workbook instance
            data_dict: Dict with brand data
            selected_date: Report date (YYYY-MM-DD)
            user_email: User email
            brands_to_export: List of (brand_name, brand_data) tuples

        Returns:
            None (modifies wb in place)
        """
        try:
            from openpyxl.styles import Font, Alignment, PatternFill, Border
        except ImportError:
            raise ImportError("openpyxl package is required")

        title_font = Font(bold=True, size=16, color="000000")
        header_font = Font(bold=True, size=11, color="000000")
        header_fill = PatternFill(fill_type=None)
        summary_fill = PatternFill(fill_type=None)
        total_fill = PatternFill(fill_type=None)
        border = Border()

        first_sheet = True
        for brand_name, data in brands_to_export:
            if first_sheet:
                ws = wb.active
                ws.title = f"{brand_name} Report"
                first_sheet = False
            else:
                ws = wb.create_sheet(title=f"{brand_name} Report")

            try:
                ws.sheet_view.showGridLines = False
            except Exception:
                pass

            self._write_header(ws, brand_name, selected_date, user_email, title_font)
            current_row = self._write_summary(ws, data, summary_fill, border, header_font)
            current_row = self._write_debit_section(
                ws, data, current_row, header_font, header_fill, border, total_fill
            )
            current_row = self._write_credit_section(
                ws, data, current_row, header_font, header_fill, border, total_fill
            )

            ws.column_dimensions['A'].width = 35
            ws.column_dimensions['B'].width = 18
            ws.column_dimensions['C'].width = 12
            ws.column_dimensions['D'].width = 5

    def _write_header(self, ws, brand_name, selected_date, user_email, title_font):
        """Write report header section.

        Args:
            ws: Worksheet
            brand_name: Brand name
            selected_date: Report date
            user_email: User email
            title_font: Title font style
        """
        from openpyxl.styles import Font, Alignment

        ws.merge_cells('A1:D1')
        ws['A1'] = f"Daily Cash Report - {brand_name}"
        ws['A1'].font = title_font
        ws['A1'].alignment = Alignment(horizontal='center')

        ws['A3'] = "Date:"
        ws['B3'] = selected_date
        ws['A4'] = "Branch:"
        ws['B4'] = self.branch
        ws['A5'] = "Corporation:"
        ws['B5'] = self.corporation
        ws['A6'] = "User:"
        ws['B6'] = user_email
        ws['A7'] = "Generated:"
        ws['B7'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for row in range(3, 8):
            ws.cell(row=row, column=1).font = Font(bold=True)

    def _write_summary(self, ws, data, summary_fill, border, header_font):
        """Write summary section.

        Args:
            ws: Worksheet
            data: Brand data
            summary_fill: Fill style
            border: Border style
            header_font: Header font

        Returns:
            int: Current row after summary
        """
        from openpyxl.styles import Font, Alignment

        current_row = 9

        ws.merge_cells(f'A{current_row}:D{current_row}')
        summary_header = ws.cell(row=current_row, column=1)
        summary_header.value = "Summary"
        summary_header.font = Font(bold=True, size=14, color="000000")
        summary_header.fill = summary_fill
        summary_header.alignment = Alignment(horizontal='center')
        current_row += 1

        summary_items = [
            ("Beginning Balance", data["beginning_balance"]),
            ("Ending Balance", data["ending_balance"]),
            ("Cash Count", data["cash_count"]),
            ("Variance", data["variance"]),
        ]

        for label, value in summary_items:
            label_cell = ws.cell(row=current_row, column=1)
            label_cell.value = label
            label_cell.font = Font(bold=True, color="000000")
            label_cell.border = border

            value_cell = ws.cell(row=current_row, column=2)
            value_cell.value = value
            value_cell.number_format = '#,##0.00'
            value_cell.alignment = Alignment(horizontal='right')
            value_cell.border = border

            if label == "Variance":
                status_cell = ws.cell(row=current_row, column=3)
                if value > 0:
                    status_cell.value = "(Over)"
                elif value < 0:
                    status_cell.value = "(Short)"
                else:
                    status_cell.value = "(Balanced)"
                status_cell.font = Font(bold=True, color="000000")
                status_cell.border = border

            current_row += 1

        return current_row + 1

    def _write_debit_section(self, ws, data, current_row, header_font, header_fill, border, total_fill):
        """Write debit (cash receipt) section.

        Args:
            ws: Worksheet
            data: Brand data
            current_row: Starting row
            header_font: Header font
            header_fill: Header fill
            border: Border style
            total_fill: Total fill style

        Returns:
            int: Current row after section
        """
        from openpyxl.styles import Font, Alignment

        if not data["debit"]:
            return current_row

        for col, hdr in enumerate(["Field", "Amount", "Lotes", ""], 1):
            cell = ws.cell(row=current_row, column=col)
            cell.value = hdr
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        current_row += 1

        debit_total = 0.0
        for label, amount, lotes in data["debit"]:
            debit_total += amount
            ws.cell(row=current_row, column=1).value = label
            ws.cell(row=current_row, column=1).border = border

            amount_cell = ws.cell(row=current_row, column=2)
            amount_cell.value = amount
            amount_cell.number_format = '#,##0.00'
            amount_cell.alignment = Alignment(horizontal='right')
            amount_cell.border = border

            lotes_cell = ws.cell(row=current_row, column=3)
            lotes_cell.value = lotes if lotes else "-"
            lotes_cell.alignment = Alignment(horizontal='center')
            lotes_cell.border = border

            current_row += 1

        total_label = ws.cell(row=current_row, column=1)
        total_label.value = "Total Cash Receipt"
        total_label.font = Font(bold=True, color="000000")
        total_label.fill = total_fill
        total_label.border = border

        total_amount = ws.cell(row=current_row, column=2)
        total_amount.value = debit_total
        total_amount.number_format = '#,##0.00'
        total_amount.font = Font(bold=True)
        total_amount.fill = total_fill
        total_amount.alignment = Alignment(horizontal='right')
        total_amount.border = border

        ws.cell(row=current_row, column=3).fill = total_fill
        ws.cell(row=current_row, column=3).border = border

        return current_row + 2

    def _write_credit_section(self, ws, data, current_row, header_font, header_fill, border, total_fill):
        """Write credit (cash out) section.

        Args:
            ws: Worksheet
            data: Brand data
            current_row: Starting row
            header_font: Header font
            header_fill: Header fill
            border: Border style
            total_fill: Total fill style

        Returns:
            int: Current row after section
        """
        from openpyxl.styles import Font, Alignment

        if not data["credit"]:
            return current_row

        for col, hdr in enumerate(["Field", "Amount", "Lotes", ""], 1):
            cell = ws.cell(row=current_row, column=col)
            cell.value = hdr
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        current_row += 1

        credit_total = 0.0
        for label, amount, lotes in data["credit"]:
            credit_total += amount
            ws.cell(row=current_row, column=1).value = label
            ws.cell(row=current_row, column=1).border = border

            amount_cell = ws.cell(row=current_row, column=2)
            amount_cell.value = amount
            amount_cell.number_format = '#,##0.00'
            amount_cell.alignment = Alignment(horizontal='right')
            amount_cell.border = border

            lotes_cell = ws.cell(row=current_row, column=3)
            lotes_cell.value = lotes if lotes else "-"
            lotes_cell.alignment = Alignment(horizontal='center')
            lotes_cell.border = border

            current_row += 1

        total_label = ws.cell(row=current_row, column=1)
        total_label.value = "Total Cash Out"
        total_label.font = Font(bold=True, color="000000")
        total_label.fill = total_fill
        total_label.border = border

        total_amount = ws.cell(row=current_row, column=2)
        total_amount.value = credit_total
        total_amount.number_format = '#,##0.00'
        total_amount.font = Font(bold=True)
        total_amount.fill = total_fill
        total_amount.alignment = Alignment(horizontal='right')
        total_amount.border = border

        ws.cell(row=current_row, column=3).fill = total_fill
        ws.cell(row=current_row, column=3).border = border

        return current_row + 2
