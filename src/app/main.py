import pandas as pd
from lib.audit.Beneish import BeneishMScoreCalculator

# Sample financial data for a single company over multiple years
data = {
    'Year': [2020, 2021, 2022],
    'Net Receivables': [1000, 1200, 1500],
    'Sales': [5000, 6000, 7000],
    'Cost of Goods Sold': [3000, 3600, 4200],
    'Current Assets': [2000, 2400, 2800],
    'PPE': [8000, 8500, 9000],
    'Net PPE': [7000, 7400, 7800],
    'Securities': [0, 0, 0],  # Assuming no securities
    'Total Assets': [15000, 16000, 17000],
    'Depreciation Expense': [500, 550, 600],
    'SG&A Expenses': [400, 450, 500],
    'Total Debt': [5000, 5500, 6000],
    'Income from Continuing Operations': [1000, 1100, 1200],
    'Cash from Operations': [800, 900, 1000]
}

df = pd.DataFrame(data)

calculator = BeneishMScoreCalculator(df)

results = calculator.get_results()

print(results)