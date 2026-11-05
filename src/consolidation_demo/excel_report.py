"""Create a portable, values-only XLSX with standard Excel Web features."""
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from .consolidation import ConsolidationResult

MONEY = '#,##0.00;[Red](#,##0.00);"—"'
NAVY = "17324D"


def write_table(ws, frame: pd.DataFrame, start: int = 4) -> int:
    """Write a readable table, preserving numeric types and explicit units."""
    for col, name in enumerate(frame.columns, 1):
        cell = ws.cell(start, col, str(name).replace("_", " ").title())
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(color="FFFFFF", bold=True)
    for row_index, values in enumerate(frame.itertuples(index=False, name=None), start + 1):
        for col, value in enumerate(values, 1):
            if hasattr(value, "item"):
                value = value.item()
            cell = ws.cell(row_index, col, value)
            key = str(frame.columns[col - 1])
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                cell.number_format = "0.0%" if key in {"ownership", "minority_percentage"} else MONEY
                if key.startswith("rate"):
                    cell.number_format = "0.0000"
            if row_index % 2:
                cell.fill = PatternFill("solid", fgColor="EFF4F8")
        first_value = str(values[0])
        if first_value.startswith("Total") or first_value in {"Net income", "Operating profit", "Balance check"}:
            for total_cell in ws[row_index][:len(frame.columns)]:
                total_cell.font = Font(bold=True, color=NAVY)
    return start + len(frame) + 2


def export_workbook(data: dict[str, pd.DataFrame], result: ConsolidationResult, path: Path) -> Path:
    """Export all eight report sheets without macros, external links or formulas."""
    book = Workbook()
    book.remove(book.active)
    titles = ["Dashboard", "Entities", "Trial Balances", "FX Rates", "Intercompany Matching",
              "Consolidation Adjustments", "Consolidated P&L", "Consolidated Balance Sheet"]
    for title in titles:
        ws = book.create_sheet(title)
        ws.cell(1, 1, title).font = Font(size=20, bold=True, color=NAVY)
        ws.cell(2, 1, "Synthetic educational portfolio demonstration | EUR reporting | Year ended 31 December 2025")
        ws.freeze_panes = "B5"
        ws.sheet_view.showGridLines = False
    dashboard = book["Dashboard"]
    labels = {"revenue": "Group Revenue (EUR)", "operating_profit": "Operating Profit (EUR)",
              "net_income": "Net Income (EUR)", "assets": "Total Assets (EUR)",
              "equity": "Total Equity incl. NCI (EUR)", "entities": "Number of entities",
              "currencies": "Number of currencies", "service_transactions": "Service transactions (count)",
              "service_value": "Service transactions (EUR)", "balance_pairs": "Outstanding balance pairs (count)",
              "balance_value": "Outstanding balances (EUR; same invoice)", "journals": "Consolidation journals (count)",
              "adjustment_debits": "Adjustment debits (EUR; equals credits)",
              "minority_profit": "Minority share of profit (EUR)", "minority_equity": "Closing minority equity (EUR)"}
    row = write_table(dashboard, pd.DataFrame([(label, result.metrics[key]) for key, label in labels.items()],
                                             columns=["Metric", "Value"]))
    for key in ("entities", "currencies", "service_transactions", "balance_pairs", "journals"):
        dashboard.cell(5 + list(labels).index(key), 2).number_format = "0"
    dashboard.cell(row, 1, "Consolidation Controls").font = Font(size=14, bold=True, color=NAVY)
    row = write_table(dashboard, pd.DataFrame(result.controls.items(), columns=["Control", "Status"]), row + 1)
    dashboard.cell(row, 1, "Minority interest allocation (EUR)").font = Font(size=14, bold=True, color=NAVY)
    row = write_table(dashboard, result.minority, row + 1)
    notes = ["Consolidation flow", "Source data → validation → FX translation → intercompany matching → journals",
             "→ eliminations → minority allocation → consolidated statements → management summary",
             "GBP 1 = EUR 1.20 at opening, average and closing; no currency translation reserve in V1.",
             "Operating profit equals net income: no tax or financing costs in this simplified model.",
             "Synthetic data and simplified assumptions; no claim of full French GAAP or IFRS compliance.",
             "Values calculated in Python. Edit CSV inputs and rerun python main.py to refresh."]
    for note in notes:
        dashboard.cell(row, 1, note)
        row += 1
    write_table(book["Entities"], data["entities"])
    write_table(book["Trial Balances"], result.translated)
    write_table(book["FX Rates"], data["fx_rates"])
    write_table(book["Intercompany Matching"], result.matching)
    adjustments = result.journals.copy()
    adjustments["debit_eur"] = adjustments.amount_eur.clip(lower=0)
    adjustments["credit_eur"] = -adjustments.amount_eur.clip(upper=0)
    row = write_table(book["Consolidation Adjustments"], adjustments)
    totals = adjustments.groupby("journal_id")[["debit_eur", "credit_eur"]].sum().reset_index()
    totals["difference_eur"] = totals.debit_eur - totals.credit_eur
    write_table(book["Consolidation Adjustments"], totals, row)
    write_table(book["Consolidated P&L"], result.pnl)
    write_table(book["Consolidated Balance Sheet"], result.balance_sheet)
    for ws in book:
        if ws.title == "Trial Balances":
            ws.auto_filter.ref = f"A4:{get_column_letter(ws.max_column)}{4 + len(result.translated)}"
        for column in ws.columns:
            width = max(len(str(cell.value or "")) for cell in column)
            ws.column_dimensions[column[0].column_letter].width = min(max(width + 2, 16), 54)
        ws.column_dimensions["A"].width = 54
        ws.row_dimensions[1].height = 32
        ws.print_options.horizontalCentered = True
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.orientation = "landscape"
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.fitToWidth = 1
        for cells in ws:
            for cell in cells:
                cell.alignment = Alignment(vertical="center")
    path.parent.mkdir(parents=True, exist_ok=True)
    book.save(path)
    return path
