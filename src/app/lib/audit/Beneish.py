import numpy as np
import pandas as pd


class BeneishMScoreCalculator:
    """
    A class to calculate the Beneish M-Score for detecting earnings manipulation
    using financial statement data.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initializes the BeneishMScoreCalculator with a DataFrame containing financial data.

        Parameters:
        df (pd.DataFrame): A DataFrame containing the financial data with the required columns.
        """
        self.df = df.copy()
        self._prepare_data()
        self._compute_previous_years()
        self._calculate_indices()
        self._compute_m_score()

    def _prepare_data(self):
        """
        Prepares the DataFrame by sorting, setting indices, and handling missing data.
        """
        # Ensure the DataFrame is sorted by Company and Year for orderly calculation
        if "Company" in self.df.columns:
            self.df = self.df.sort_values(by=["Company", "Year"]).reset_index(drop=True)
            self.df.set_index(["Company", "Year"], inplace=True)
        else:
            self.df = self.df.sort_values(by=["Year"]).reset_index(drop=True)
            self.df.set_index(["Year"], inplace=True)

        # Handle missing 'Securities' data by setting it to zero if not provided
        if "Securities" not in self.df.columns:
            self.df["Securities"] = 0

    def _compute_previous_years(self):
        """
        Computes previous year's financial data for index calculations.
        """
        if "Company" in self.df.index.names:
            grouped = self.df.groupby(level="Company")
        else:
            grouped = self.df

        # Shift financial data to get previous year's figures
        financial_fields = [
            "Net Receivables",
            "Sales",
            "Cost of Goods Sold",
            "Current Assets",
            "PPE",
            "Net PPE",
            "Securities",
            "Total Assets",
            "Depreciation Expense",
            "SG&A Expenses",
            "Total Debt",
            "Income from Continuing Operations",
            "Cash from Operations",
        ]

        for field in financial_fields:
            self.df[f"{field}_prev"] = grouped[field].shift(1)

    def _calculate_indices(self):
        """
        Calculates the Beneish M-Score components.
        """
        df = self.df

        # DSRI: Days Sales in Receivables Index
        df["DSRI"] = (df["Net Receivables"] / df["Sales"]) / (
            df["Net Receivables_prev"] / df["Sales_prev"]
        )

        # GMI: Gross Margin Index
        df["Gross_Margin"] = (df["Sales"] - df["Cost of Goods Sold"]) / df["Sales"]
        df["Gross_Margin_prev"] = (
            df["Sales_prev"] - df["Cost of Goods Sold_prev"]
        ) / df["Sales_prev"]
        df["GMI"] = df["Gross_Margin_prev"] / df["Gross_Margin"]

        # AQI: Asset Quality Index
        df["Asset_Quality"] = (
            1
            - (df["Current Assets"] + df["Net PPE"] + df["Securities"])
            / df["Total Assets"]
        )
        df["Asset_Quality_prev"] = (
            1
            - (df["Current Assets_prev"] + df["Net PPE_prev"] + df["Securities_prev"])
            / df["Total Assets_prev"]
        )
        df["AQI"] = df["Asset_Quality"] / df["Asset_Quality_prev"]

        # SGI: Sales Growth Index
        df["SGI"] = df["Sales"] / df["Sales_prev"]

        # DEPI: Depreciation Index
        df["Depreciation_Rate"] = df["Depreciation Expense"] / (
            df["Depreciation Expense"] + df["Net PPE"]
        )
        df["Depreciation_Rate_prev"] = df["Depreciation Expense_prev"] / (
            df["Depreciation Expense_prev"] + df["Net PPE_prev"]
        )
        df["DEPI"] = df["Depreciation_Rate_prev"] / df["Depreciation_Rate"]

        # SGAI: SG&A Expenses Index
        df["SGAI"] = (df["SG&A Expenses"] / df["Sales"]) / (
            df["SG&A Expenses_prev"] / df["Sales_prev"]
        )

        # LVGI: Leverage Index
        df["LVGI"] = (df["Total Debt"] / df["Total Assets"]) / (
            df["Total Debt_prev"] / df["Total Assets_prev"]
        )

        # TATA: Total Accruals to Total Assets
        df["TATA"] = (
            df["Income from Continuing Operations"] - df["Cash from Operations"]
        ) / df["Total Assets"]

    def _compute_m_score(self):
        """
        Computes the Beneish M-Score using the calculated indices.
        """
        df = self.df
        df["M-Score"] = (
            -4.84
            + 0.92 * df["DSRI"]
            + 0.528 * df["GMI"]
            + 0.404 * df["AQI"]
            + 0.892 * df["SGI"]
            + 0.115 * df["DEPI"]
            - 0.172 * df["SGAI"]
            + 4.679 * df["TATA"]
            - 0.327 * df["LVGI"]
        )

    @staticmethod
    def classify_m_score(score: float) -> str:
        """
        Classifies the Beneish M-Score into categories.

        Parameters:
        score (float): The Beneish M-Score.

        Returns:
        str: Classification category ('Unlikely', 'Possible', 'Likely').
        """
        if score < -2.22:
            return "Unlikely"
        elif -2.22 <= score <= -1.78:
            return "Possible"
        else:
            return "Likely"

    def get_results(self) -> pd.DataFrame:
        """
        Retrieves the calculated Beneish M-Score and its components.

        Returns:
        pd.DataFrame: A DataFrame with the Beneish M-Score, its components, and classification.
        """
        df = self.df.reset_index()

        columns_to_include = (
            [
                "Company",
                "Year",
                "DSRI",
                "GMI",
                "AQI",
                "SGI",
                "DEPI",
                "SGAI",
                "TATA",
                "LVGI",
                "M-Score",
            ]
            if "Company" in df.columns
            else [
                "Year",
                "DSRI",
                "GMI",
                "AQI",
                "SGI",
                "DEPI",
                "SGAI",
                "TATA",
                "LVGI",
                "M-Score",
            ]
        )

        result_df = df[columns_to_include].copy()

        result_df.replace([np.inf, -np.inf], np.nan, inplace=True)

        result_df["M-Score Classification"] = result_df["M-Score"].apply(
            lambda x: self.classify_m_score(x) if pd.notnull(x) else np.nan
        )

        return result_df
