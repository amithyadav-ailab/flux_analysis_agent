# flux_analysis_agent

MCP server for flux/variance analysis over CSV data, with an optional OpenAI-backed
analysis agent for natural-language explanations.

## Setup

1) Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

2) Configure environment variables (in `.env` or your shell):

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
# OPENAI_API_BASE=https://api.openai.com/v1
# DEFAULT_THRESHOLD_PERCENT=5
# LOG_LEVEL=INFO
# PORT=8000
```

Note: `OPENAI_API_KEY` is required for the `flux_agent` tool and schema inference.
If it is not set, `flux_agent` returns an error and schema inference falls back to heuristics.

## Run the server

From this repo root:

```powershell
python server.py
```

Or from the parent directory:

```powershell
python -m flux_analysis_agent.server
```

The server uses MCP over STDIO and waits for a client to connect.

## Tools

### upload_data

Input:

```json
{
  "csv_data": "<CSV text including header>",
  "data_name": "Optional label"
}
```

Output:

```json
{
  "data_id": "data-...",
  "columns": ["account_id", "account_name", "category", "current_period_amount", "prior_period_amount"],
  "schema_summary": "Optional natural-language schema summary"
}
```

### get_analysis_result

Input:

```json
{
  "data_id": "data-...",
  "only_significant": false
}
```

Output:

```json
{
  "variances": [
    {
      "account_id": "ACC-1001",
      "account_name": "Cash and Cash Equivalents",
      "category": "Assets",
      "current_period_amount": 55000.0,
      "prior_period_amount": 50000.0,
      "change_amount": 5000.0,
      "change_percent": 10.0,
      "exceeds_threshold": true,
      "je_details": "Sale of investment",
      "operational_drivers": "Liquidation of short-term investments increased cash"
    }
  ]
}
```

### flux_agent

Input:

```json
{
  "data_id": "data-...",
  "query": "Explain the major changes."
}
```

Output:

```json
{
  "explanation": "A grounded explanation based on the dataset."
}
```

## Sample CSV

```csv
account_id,account_name,category,current_period_amount,prior_period_amount,threshold_type,threshold_value,je_details,operational_drivers
ACC-1001,Cash and Cash Equivalents,Assets,55000,50000,percentage,5,Sale of investment,Liquidation of short-term investments increased cash
ACC-1015,Accounts Receivable,Assets,120000,118000,percentage,5,,
ACC-2001,Accounts Payable,Liabilities,42000,50000,absolute,6000,,Faster supplier payments
```

## Notes

- Data is stored in memory only (not persisted).
- Thresholds are read from `threshold_type`/`threshold_value` columns per row.
- If no thresholds are provided, `DEFAULT_THRESHOLD_PERCENT` can be used.