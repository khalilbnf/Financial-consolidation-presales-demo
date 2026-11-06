# Financial Consolidation Presales Demo

A Python and Excel portfolio project demonstrating a simplified multi-entity consolidation workflow including FX translation, intercompany eliminations, minority interests and consolidated financial reporting.

**This project uses synthetic data and simplified assumptions for educational and portfolio purposes. It is not intended to provide full French GAAP or IFRS compliance.** This is a fictional demonstration, not previous client work.

## Objective

Show how financial concepts can become understandable software requirements, controlled calculations and reviewable management reports. Finance reviewers can follow the workbook; technical reviewers can inspect small Python modules and business-focused tests. Customer discovery and solution mapping connect the implementation to a fictional finance team's needs.

## Business scenario and results

For the year ended 31 December 2025, France Parent SAS consolidates Germany GmbH (80% owned, EUR) and UK Ltd (100% owned, GBP). Group reporting currency is EUR. The parent fully consolidates both subsidiaries and separately allocates minority interests.

| Consolidated measure | EUR |
|---|---:|
| Revenue | 4,460,000 |
| Operating expenses | 3,840,000 |
| Operating profit / net income | 620,000 |
| Profit attributable to parent | 580,000 |
| Profit attributable to minority interests | 40,000 |
| Assets | 4,040,000 |
| Liabilities | 1,220,000 |
| Total equity | 2,820,000 |
| Equity attributable to parent | 2,580,000 |
| Closing minority equity | 240,000 |

Assets = liabilities + equity. Three consolidation journals balance individually; total journal debits and credits are each €2,300,000. Journal volume is not a measure of profit impact.

## Workflow

Source CSVs → validation → FX translation → intercompany matching → consolidation adjustments → eliminations → minority interest allocation → consolidated P&L and balance sheet → dashboard.

Validation rejects missing values, duplicates, unknown entities, invalid ownership/currencies, missing FX, unbalanced trial balances, unmatched intercompany records and unsupported model assumptions. Intercompany detail must reconcile to the relevant trial-balance accounts. Failed checks stop generation with a logged error and nonzero exit status. A previously generated workbook is not refreshed on a failed run.

## Install and run

Requires Python 3.10 or newer. No Excel Desktop, LLM, paid API or network service is used by the pipeline. Network access is only needed to install dependencies.

From this project's directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
python -m pytest -q
```

If PowerShell activation is restricted, use `.\.venv\Scripts\python.exe main.py` and `.\.venv\Scripts\python.exe -m pytest -q` directly. On macOS/Linux, activate with `source .venv/bin/activate`.

The project was verified with Python 3.13, pandas 3.1.1, openpyxl 3.1.5 and pytest 9.2.0. Calculations are deterministic; generated ZIP metadata can differ between workbook runs. Input and output paths resolve relative to `main.py`, so execution does not depend on the shell's working directory.

## Generated workbook

[`output/French_Consolidation_Demo.xlsx`](output/French_Consolidation_Demo.xlsx) contains:

1. Dashboard: financial KPIs, five Consolidation Controls, minority allocation and workflow.
2. Entities: scope, currency and ownership.
3. Trial Balances: original amounts, account classifications, rate types, applied FX and EUR values.
4. FX Rates: synthetic opening, average and closing rates.
5. Intercompany Matching: both local sides, currencies, rates, EUR values and differences.
6. Consolidation Adjustments: journal explanations, signed postings, debits/credits and journal checks.
7. Consolidated P&L: group profit and attribution.
8. Consolidated Balance Sheet: account totals, parent/NCI equity and balance check.

Values are calculated in Python. Edit the CSVs and rerun the pipeline to refresh; changing cells in the report does not recalculate consolidation. Standard XLSX formatting, numeric values and frozen panes support Excel Web. There are no macros, formulas requiring recalculation, external links or desktop-specific connections. Automated tests reopen the workbook and inspect the ZIP/XML package. Excel Web rendering has not been directly tested in this environment.

## Accounting examples

**FX:** GBP 1 = EUR 1.20 for opening, average and closing rates. UK revenue £800,000 becomes €960,000. P&L uses average rates, assets/liabilities closing rates, and opening equity/investments opening rates. Equal rates intentionally avoid a currency translation reserve; unequal rates are rejected in V1.

**Intercompany:** France's €500,000 service revenue and Germany's €500,000 expense are both eliminated. The €200,000 remaining receivable/payable is eliminated separately. One invoice plus its outstanding balance gives two matched pairs, not two sales. There is no group profit impact from these eliminations.

**Investment and minority interests:** €1.4m parent investments are eliminated against €1.6m subsidiary opening equity, recognizing €200k opening NCI. Germany profit €200k × 20% = €40k minority profit; closing NCI is €240k. No goodwill arises under the agreed opening book-value assumption.

See [accounting assumptions and reconciliations](docs/accounting_assumptions.md) for the complete calculation trail.

## Architecture and technologies

```text
data/                         Four versioned synthetic CSV inputs
src/consolidation_demo/
  data_loader.py              CSV input
  validations.py              Schema, reference and accounting checks
  fx_translation.py           Traceable local-to-EUR conversion
  intercompany.py             Matching and elimination journals
  consolidation.py            Investment elimination, statements, controls
  minority_interest.py        Ownership and NCI allocations
  excel_report.py             Standard XLSX presentation
customer_demo/                Discovery, requirements, mapping, demo script
docs/                         Accounting assumptions and file manifest
tests/                        Financial expectations and failure cases
output/                       Generated deliverable
main.py                       Command-line entry point
```

Python, pandas, openpyxl, pytest, pathlib and standard Python logging. pandas supplies NumPy as a dependency; validation uses it to reject non-finite numeric inputs. Modules have explicit responsibilities without a database or service layer.

## Tests

Run `python -m pytest -q`. The suite covers translation, reciprocal matching, elimination signs and values, ownership, profit/equity NCI, all approved consolidated totals, balanced journals, the consolidated balance-sheet equation, invalid input cases, unsupported investment assumptions and workbook portability. The verified V1 suite contains **23 passing tests**.

## Customer / presales material

- [Discovery questions](customer_demo/discovery_questions.md)
- [Fictional customer requirements](customer_demo/customer_requirements.md)
- [Solution mapping](customer_demo/solution_mapping.md)
- [Practical demo scenario](customer_demo/demo_scenario.md)

## Screenshots

Open the generated workbook in Excel Web and capture the Dashboard, Intercompany Matching and consolidated statements for a GitHub preview. Screenshots are not included in V1; the workbook is the actual deliverable. Avoid including personal account details in captures.

## Limitations

One period, directly controlled subsidiaries, constant ownership, equal FX rates, no dividends and no other equity movements. No goodwill, tax/deferred tax, financing costs, OCI, unrealized inventory profit, acquisition changes, multi-tier consolidation, statutory disclosures or cash-flow statement. Operating profit equals net income. The internal account codes are educational classifications, not a complete French statutory chart.

No production authorization, approval workflow, immutable audit log or source-system integration. Inputs are trusted local files subject to validation. Monetary calculations use cent-rounded numeric values suitable for these synthetic examples, not a production accounting precision engine. Business benefits are expected opportunities, not measured outcomes.

## Repository status

Prepared for GitHub publication with source, tests, synthetic data, generated workbook, documentation, ignore rules and an MIT license. The local virtual environment and caches are excluded. No remote repository has been created and nothing has been published. See the [file manifest](docs/file_manifest.md).
