# Accounting assumptions and audit trail

This project uses synthetic data and simplified assumptions for educational and portfolio purposes. It is not intended to provide full French GAAP or IFRS compliance. It is not previous client work.

## Scope and signs

The fictional period is the year ended 31 December 2025. All subsidiaries are directly controlled for the entire year. Germany is 80% owned and UK is 100% owned. Full consolidation includes 100% of each subsidiary; NCI is an allocation, not a reduction in consolidated revenue or assets.

Trial balances use debit-positive and credit-negative amounts. Assets and expenses normally carry debits; liabilities, opening equity and revenue carry credits. Current profit is calculated from revenue and expense accounts and added to opening equity in the balance sheet. It is not posted a second time into source equity. Account 1300 is the parent's combined investment; 3000 is opening equity; 3100 is opening NCI created by consolidation.

## FX

Rates are EUR per local currency unit. GBP opening, average and closing rates are all 1.20; EUR rates are all 1.00. P&L uses average rates, assets/liabilities use closing rates, equity and investments use opening rates. £800,000 UK revenue becomes €960,000; £100,000 UK profit becomes €120,000. Equal rates intentionally avoid a currency translation reserve. V1 rejects unequal rates rather than silently omitting a reserve. Amounts are rounded to cents per translated line, with a half-cent control tolerance. This is a readable educational calculation using rounded numbers, not a production decimal accounting engine.

## Internal service and balance

France sells €500,000 of services to Germany, consumed in the current year. France records credit revenue and Germany debit expense. €200,000 remains unpaid: France debit receivable, Germany credit payable. These are the same invoice and its remaining balance, not €700,000 of economic sales. Matching requires two reciprocal, opposite-signed EUR entries and agreement to the mapped trial-balance accounts.

IC-SERVICE-001 debits revenue €500,000 and credits expense €500,000. IC-BALANCE-001 credits receivables €200,000 and debits payables €200,000. Neither entry changes group profit. There is no inventory or unrealized margin elimination.

## Investment elimination and NCI

Germany opening net assets are €1,000,000; the parent's investment is €800,000. UK opening net assets are £500,000 (€600,000); the investment is €600,000. Acquisition cost equals the parent's share of opening book net assets. There is no goodwill, acquisition-date fair-value adjustment or pre/post-acquisition split.

INV-001 debits subsidiary opening equity €1,600,000, credits investments €1,400,000 and credits opening NCI €200,000. All journals balance individually. Total adjustment debits are €2,300,000, equal to credits; this is journal volume, not a profit impact.

Germany profit €200,000 × 20% gives €40,000 NCI profit. Opening NCI €200,000 + profit €40,000 gives closing NCI €240,000. Parent share of Germany profit is €160,000. Consolidated profit €620,000 less NCI profit €40,000 gives parent profit €580,000. No dividends, ownership changes or other equity movements occur. The service seller is wholly owned; no upstream unrealized-profit allocation arises.

## Reconciliations

Revenue: €2,500,000 + €1,500,000 + £800,000 × 1.20 − €500,000 = €4,460,000.

Expenses: €2,200,000 + €1,300,000 + £700,000 × 1.20 − €500,000 = €3,840,000.

Profit: €4,460,000 − €3,840,000 = €620,000.

Assets: €3,300,000 + €1,500,000 + £700,000 × 1.20 − €200,000 − €1,400,000 = €4,040,000.

Liabilities: €1,000,000 + €300,000 + £100,000 × 1.20 − €200,000 = €1,220,000.

Equity: parent opening equity €2,000,000 + opening NCI €200,000 + group profit €620,000 = €2,820,000. Parent equity is €2,580,000; closing NCI is €240,000. Assets equal liabilities plus equity.

## Intentional exclusions

No tax, deferred tax, financing costs, goodwill, OCI, changing FX rates, statutory disclosures, cash-flow statement, ownership changes, multi-tier ownership, joint ventures or associates. Operating profit equals net income. No claim of complete French accounting chart mapping or statutory French consolidation. The workbook is a generated report, not an interactive calculation engine; edit inputs and rerun Python.
