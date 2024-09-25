import pandas as pd
import pymupdf

from lib.Chatbot import Chatbot
from lib.audit.Beneish import BeneishMScoreCalculator

doc = pymupdf.open("../test/pdf/financial_report_5_years.pdf")
text = str(pymupdf.get_text(doc))

chatbot = Chatbot()
financial_data = chatbot.extract_financial_data(text)
df = pd.DataFrame(financial_data)

calculator = BeneishMScoreCalculator(df)

results = calculator.get_results()
print(results)
