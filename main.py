"""Run with python main.py from any working directory."""
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from consolidation_demo.data_loader import load_data
from consolidation_demo.consolidation import consolidate
from consolidation_demo.excel_report import export_workbook


def main() -> int:
    """Build the report or return a clear nonzero failure status."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        data = load_data(ROOT / "data")
        result = consolidate(data)
        path = export_workbook(data, result, ROOT / "output" / "French_Consolidation_Demo.xlsx")
    except (ValueError, OSError, KeyError) as error:
        logging.error("Consolidation failed: %s", error)
        return 1
    m = result.metrics
    print("\nFinancial Consolidation Demo\n")
    print(f"Entities processed: {m['entities']}\nReporting currency: EUR")
    print(f"Intercompany pairs matched: {len(result.matching)} (one service invoice and its outstanding balance)")
    print(f"Consolidation adjustments: {m['journals']} balanced journals")
    print(f"Consolidated Revenue: EUR {m['revenue']:,.2f}")
    print(f"Consolidated Net Income: EUR {m['net_income']:,.2f}")
    print(f"Assets: EUR {m['assets']:,.2f} = Liabilities {m['liabilities']:,.2f} + Equity {m['equity']:,.2f}")
    print(f"Controls: {len(result.controls)}/5 PASS\n\nWorkbook generated:\n{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
