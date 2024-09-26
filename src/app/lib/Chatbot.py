import json
from llama_cpp import Llama

class Chatbot:
    SYSTEM_PROMPT = (
        "You are a specialized chatbot designed to convert financial data from PDF documents into a structured JSON format. "
        "Your primary function is to extract relevant information from the provided PDF content and organize it into the following JSON structure:\n"
        "{\n"
        '    "Year": <array of years>,\n'
        '    "Net Receivables": <array of net receivables>,\n'
        '    "Sales": <array of sales>,\n'
        '    "Cost of Goods Sold": <array of cost of goods sold>,\n'
        '    "Current Assets": <array of current assets>,\n'
        '    "PPE": <array of PPE>,\n'
        '    "Net PPE": <array of net PPE>,\n'
        '    "Securities": <array of securities, if not available, use 0>,\n'
        '    "Total Assets": <array of total assets>,\n'
        '    "Depreciation Expense": <array of depreciation expenses>,\n'
        '    "SG&A Expenses": <array of SG&A expenses>,\n'
        '    "Total Debt": <array of total debt>,\n'
        '    "Income from Continuing Operations": <array of income from continuing operations>,\n'
        '    "Cash from Operations": <array of cash from operations>\n'
        "}\n"
        'Write ONLY JSON data without codeblock to the standard output. The JSON data should be formatted as a single line without any leading or trailing whitespaces.\n'
        'write "END" in new line to finish the conversation.'
    )

    def __init__(self, model_path=None, n_gpu_layers=-1, n_ctx=4096, verbose=True):
        self.model_path = model_path or "./model/llm/14b/aidit-14b-instruct-q4_k_m-00001-of-00003.gguf"
        self.llm = Llama(
            model_path=self.model_path,
            n_gpu_layers=n_gpu_layers,
            n_ctx=n_ctx,
            verbose=verbose,
        )

    def extract_financial_data(self, text):
        prompt = f"{self.SYSTEM_PROMPT}\n{text}"
        output = self.llm.create_completion(
            prompt=prompt,
            echo=False,
            max_tokens=None,
            stream=False,
            stop=["END"],
        )
        answer = output['choices'][0]['text'].strip()
        try:
            return json.loads(answer)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}")
