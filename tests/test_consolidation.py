"""Business expectations and failure cases for the synthetic reference model."""
from pathlib import Path
from zipfile import ZipFile
import pytest
from openpyxl import load_workbook
from consolidation_demo.data_loader import load_data
from consolidation_demo.validations import validate_data
from consolidation_demo.fx_translation import translate
from consolidation_demo.intercompany import match_intercompany, elimination_journals
from consolidation_demo.consolidation import consolidate
from consolidation_demo.excel_report import export_workbook

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def data():
    return load_data(ROOT / "data")


def test_fx_translation(data):
    translated = translate(data["trial_balances"], data["fx_rates"])
    uk_revenue = translated[(translated.entity_id == "UK") & (translated.account_code == "4000")].iloc[0]
    assert uk_revenue.amount == -800000
    assert uk_revenue.rate == 1.2
    assert uk_revenue.amount_eur == -960000


def test_matching_and_elimination(data):
    matches = match_intercompany(data["intercompany"], data["fx_rates"])
    assert matches.amount_eur.tolist() == [200000, 500000]
    assert matches.difference_eur.eq(0).all()
    journals = elimination_journals(data["intercompany"], data["fx_rates"], data["trial_balances"])
    assert journals.groupby("journal_id").amount_eur.sum().eq(0).all()
    expected = {"4100": 500000, "5100": -500000, "1200": -200000, "2100": 200000}
    assert journals.set_index("account_code").amount_eur.to_dict() == expected


def test_ownership_and_minority(data):
    minority = consolidate(data).minority.set_index("entity_id")
    de = minority.loc["DE"]
    assert de.ownership == 0.8
    assert de.minority_percentage == 0.2
    assert de.net_income == 200000
    assert de.parent_profit == 160000
    assert de.minority_profit == 40000
    assert de.opening_minority == 200000
    assert de.closing_minority == 240000
    assert minority.loc["UK", "closing_minority"] == 0


def test_consolidated_totals_and_controls(data):
    result = consolidate(data)
    expected = dict(revenue=4460000, operating_profit=620000, net_income=620000,
                    parent_profit=580000, minority_profit=40000, assets=4040000,
                    liabilities=1220000, equity=2820000, parent_equity=2580000,
                    minority_equity=240000, adjustment_debits=2300000, journals=3)
    for key, value in expected.items():
        assert result.metrics[key] == value, key
    assert result.metrics["assets"] == result.metrics["liabilities"] + result.metrics["equity"]
    assert result.journals.groupby("journal_id").amount_eur.sum().eq(0).all()
    assert set(result.controls.values()) == {"PASS"}
    assert result.balance_sheet.iloc[-1].EUR == 0


@pytest.mark.parametrize("case", ["missing_entity", "missing_account", "unknown_entity", "currency",
    "missing_fx", "duplicate", "ownership", "imbalance", "ic_mismatch", "blank", "nan",
    "fx_difference", "ic_tb_difference", "bad_counterparty", "duplicate_fx", "missing_column"])
def test_invalid_data(data, case):
    tb, entities, rates, ic = (data[k] for k in ("trial_balances", "entities", "fx_rates", "intercompany"))
    if case == "missing_entity": tb.loc[0, "entity_id"] = None
    elif case == "missing_account": tb.loc[0, "account_code"] = None
    elif case == "unknown_entity": tb.loc[0, "entity_id"] = "XX"
    elif case == "currency": tb.loc[0, "currency"] = "USD"
    elif case == "missing_fx": data["fx_rates"] = rates.iloc[:-1].copy()
    elif case == "duplicate": data["trial_balances"] = tb.loc[list(tb.index) + [0]].copy()
    elif case == "ownership": entities.loc[1, "ownership"] = 1.5
    elif case == "imbalance": tb.loc[0, "amount"] += 1
    elif case == "ic_mismatch": ic.loc[0, "amount"] += 1
    elif case == "blank": tb.loc[0, "account_code"] = " "
    elif case == "nan": rates.loc[0, "rate"] = float("inf")
    elif case == "fx_difference": rates.loc[5, "rate"] = 1.3
    elif case == "ic_tb_difference": ic.loc[0:1, "amount"] *= 2
    elif case == "bad_counterparty": ic.loc[0, "counterparty_id"] = "UK"
    elif case == "duplicate_fx": data["fx_rates"] = rates.loc[list(rates.index) + [0]].copy()
    elif case == "missing_column": data["entities"] = entities.drop(columns="ownership")
    with pytest.raises(ValueError):
        validate_data(data)


def test_mismatch_reports_reference(data):
    data["intercompany"].loc[0, "amount"] += 100
    with pytest.raises(ValueError, match="SERVICE-001"):
        match_intercompany(data["intercompany"], data["fx_rates"])


def test_unsupported_investment_cost(data):
    tb = data["trial_balances"]
    tb.loc[(tb.entity_id == "FR") & (tb.account_code == "1300"), "amount"] += 100
    tb.loc[(tb.entity_id == "FR") & (tb.account_code == "1000"), "amount"] -= 100
    with pytest.raises(ValueError, match="no goodwill"):
        consolidate(data)


def test_workbook_portability_and_contents(data, tmp_path):
    result = consolidate(data)
    path = export_workbook(data, result, tmp_path / "demo.xlsx")
    book = load_workbook(path, data_only=False)
    assert book.sheetnames == ["Dashboard", "Entities", "Trial Balances", "FX Rates",
        "Intercompany Matching", "Consolidation Adjustments", "Consolidated P&L", "Consolidated Balance Sheet"]
    assert book["Consolidated P&L"]["B5"].value == 4460000
    assert book["Consolidated Balance Sheet"].cell(book["Consolidated Balance Sheet"].max_row, 2).value == 0
    assert sum(cell.value == "PASS" for row in book["Dashboard"] for cell in row) == 5
    assert not any(cell.data_type == "f" for sheet in book for row in sheet for cell in row)
    book.close()
    with ZipFile(path) as archive:
        assert archive.testzip() is None
        assert not any("vba" in name.lower() or "externalLinks" in name or "connections" in name for name in archive.namelist())
