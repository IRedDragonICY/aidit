import pandas as pd
import numpy as np

def calculate_beneish_m_score(df):
    """
    Calculates the Beneish M-Score for detecting earnings manipulation, using financial statement data.

    Parameters:
    df (pd.DataFrame): A DataFrame containing the financial data with the following columns:
        - 'Company' (optional): Name of the company.
        - 'Year': Reporting year.
        - 'Net Receivables': Net accounts receivable.
        - 'Sales': Total sales or revenue.
        - 'Cost of Goods Sold': Cost of goods sold (COGS).
        - 'Current Assets': Total current assets.
        - 'PPE': Gross property, plant, and equipment.
        - 'Net PPE': Net property, plant, and equipment (after depreciation).
        - 'Securities': Marketable securities (set to zero if not applicable).
        - 'Total Assets': Total assets.
        - 'Depreciation Expense': Depreciation expense.
        - 'SG&A Expenses': Selling, general, and administrative expenses.
        - 'Total Debt': Total debt (current liabilities + long-term debt).
        - 'Income from Continuing Operations': Income from continuing operations.
        - 'Cash from Operations': Net cash flow from operating activities.

    Returns:
    pd.DataFrame: A DataFrame with the Beneish M-Score and its components for each company and year.
    """

    # Ensure the DataFrame is sorted by Company and Year for orderly calculation
    if 'Company' in df.columns:
        df = df.sort_values(by=['Company', 'Year']).copy()
        df.set_index(['Company', 'Year'], inplace=True)
    else:
        df = df.sort_values(by=['Year']).copy()
        df.set_index(['Year'], inplace=True)

    # Handle missing 'Securities' data by setting it to zero if not provided
    if 'Securities' not in df.columns:
        df['Securities'] = 0

    # Group by company if 'Company' column exists, else treat as a single company
    if 'Company' in df.index.names:
        grouped = df.groupby(level='Company')
    else:
        grouped = df

    # Shift financial data to get previous year's figures for index calculations
    df['Receivables_prev'] = grouped['Net Receivables'].shift(1)
    df['Sales_prev'] = grouped['Sales'].shift(1)
    df['COGS_prev'] = grouped['Cost of Goods Sold'].shift(1)
    df['Current Assets_prev'] = grouped['Current Assets'].shift(1)
    df['PPE_prev'] = grouped['PPE'].shift(1)
    df['Net PPE_prev'] = grouped['Net PPE'].shift(1)
    df['Securities_prev'] = grouped['Securities'].shift(1)
    df['Total Assets_prev'] = grouped['Total Assets'].shift(1)
    df['Depreciation_prev'] = grouped['Depreciation Expense'].shift(1)
    df['SG&A Expenses_prev'] = grouped['SG&A Expenses'].shift(1)
    df['Total Debt_prev'] = grouped['Total Debt'].shift(1)
    df['Income_prev'] = grouped['Income from Continuing Operations'].shift(1)
    df['Cash Flow_prev'] = grouped['Cash from Operations'].shift(1)

    # Calculate the Beneish M-Score components
    # DSRI: Days Sales in Receivables Index
    df['DSRI'] = (df['Net Receivables'] / df['Sales']) / (df['Receivables_prev'] / df['Sales_prev'])

    # GMI: Gross Margin Index
    df['Gross Margin'] = (df['Sales'] - df['Cost of Goods Sold']) / df['Sales']
    df['Gross Margin_prev'] = (df['Sales_prev'] - df['COGS_prev']) / df['Sales_prev']
    df['GMI'] = df['Gross Margin_prev'] / df['Gross Margin']

    # AQI: Asset Quality Index
    df['Asset Quality'] = 1 - (df['Current Assets'] + df['Net PPE'] + df['Securities']) / df['Total Assets']
    df['Asset Quality_prev'] = 1 - (df['Current Assets_prev'] + df['Net PPE_prev'] + df['Securities_prev']) / df['Total Assets_prev']
    df['AQI'] = df['Asset Quality'] / df['Asset Quality_prev']

    # SGI: Sales Growth Index
    df['SGI'] = df['Sales'] / df['Sales_prev']

    # DEPI: Depreciation Index
    df['Depreciation Rate'] = df['Depreciation Expense'] / (df['Depreciation Expense'] + df['Net PPE'])
    df['Depreciation Rate_prev'] = df['Depreciation_prev'] / (df['Depreciation_prev'] + df['Net PPE_prev'])
    df['DEPI'] = df['Depreciation Rate_prev'] / df['Depreciation Rate']

    # SGAI: SG&A Expenses Index
    df['SGAI'] = (df['SG&A Expenses'] / df['Sales']) / (df['SG&A Expenses_prev'] / df['Sales_prev'])

    # LVGI: Leverage Index
    df['LVGI'] = (df['Total Debt'] / df['Total Assets']) / (df['Total Debt_prev'] / df['Total Assets_prev'])

    # TATA: Total Accruals to Total Assets
    df['TATA'] = (df['Income from Continuing Operations'] - df['Cash from Operations']) / df['Total Assets']

    # Calculate the Beneish M-Score using the coefficients from the original model
    df['M-Score'] = (
        -4.84 +
        0.92 * df['DSRI'] +
        0.528 * df['GMI'] +
        0.404 * df['AQI'] +
        0.892 * df['SGI'] +
        0.115 * df['DEPI'] -
        0.172 * df['SGAI'] +
        4.679 * df['TATA'] -
        0.327 * df['LVGI']
    )

    # Reset index to turn 'Company' and 'Year' back into columns
    df.reset_index(inplace=True)

    columns_to_return = ['Year', 'DSRI', 'GMI', 'AQI', 'SGI', 'DEPI', 'SGAI', 'TATA', 'LVGI', 'M-Score']
    if 'Company' in df.columns:
        columns_to_return.insert(0, 'Company')

    result_df = df[columns_to_return]
    result_df = result_df.replace([np.inf, -np.inf], np.nan)

    return result_df