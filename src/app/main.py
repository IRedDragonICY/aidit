import pandas as pd

from lib.audit.Beneish import BeneishMScoreCalculator
import json
import pymupdf
from llama_cpp import Llama


doc = pymupdf.open("../test/pdf/financial_report_5_years.pdf")
text = str(pymupdf.get_text(doc))
system_prompt = '''
You are a specialized chatbot designed to convert financial data from PDF documents into a structured JSON format. Your primary function is to extract relevant information from the provided PDF content and organize it into the following JSON structure:
    {
        "Year":<array of years>,
        "Net Receivables": <array of net receivables>,
        "Sales": <array of sales>,
        "Cost of Goods Sold": <array of cost of goods sold>,
        "Current Assets": <array of current assets>,
        "PPE": <array of PPE>,
        "Net PPE": <array of net PPE>,
        "Securities": <array of securities, if not available, use 0>,
        "Total Assets": <array of total assets>,
        "Depreciation Expense": <array of depreciation expenses>,
        "SG&A Expenses": <array of SG&A expenses>,
        "Total Debt": <array of total debt>,
        "Income from Continuing Operations": <array of income from continuing operations>,
        "Cash from Operations": <array of cash from operations>
    }
Write ONLY JSON data without codeblock to the standard output. The JSON data should be formatted as a single line without any leading or trailing whitespaces.
write "END" in new line to finish the conversation.
'''

model_id = "./model/llm/14b/aidit-14b-instruct-q4_k_m-00001-of-00003.gguf"

llm = Llama(
      model_path=model_id,
      n_gpu_layers = -1,
      n_ctx = 4096,
      verbose=True
)


output = llm.create_completion(
    prompt=f"{system_prompt}\n{text}",
    echo=False,
    max_tokens=None,
    stream=True,
    stop=["END"],
)

answer = ""
for item in output:
      answer+=item['choices'][0]['text']
      print(item['choices'][0]['text'], end='')

financial_data_json = answer
financial_data = json.loads(financial_data_json)
df = pd.DataFrame(financial_data)

calculator = BeneishMScoreCalculator(df)

results = calculator.get_results()
print(results)
