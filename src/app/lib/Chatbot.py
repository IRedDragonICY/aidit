import json
from llama_cpp import Llama

class Chatbot:
    EXTRACT_PROMPT = (
'''
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
    )

    AIDIT_PROMPT = (
        "You are AIdit, an AI-based audit assistant. "
        "You assist users by answering their audit-related questions in a clear and professional manner. "
        "Provide concise, accurate answers, and engage in multi-turn conversations."
        "You will answer in Indonesian. "
        "First chat, you ask user to provide file for analysis. "
    )

    def __init__(self, model_path=None, n_gpu_layers=-1, n_ctx=8192, verbose=True):
        self.model_path = model_path or "./model/llm/14b/aidit-14b-instruct-q4_k_m-00001-of-00003.gguf"
        self.llm = Llama(
            model_path=self.model_path,
            n_gpu_layers=n_gpu_layers,
            n_ctx=n_ctx,
            verbose=verbose,
        )
        self.conversation_history = []
        self.extracted_data = None

    def get_initial_greeting(self, callback=None):
        prompt = self.AIDIT_PROMPT + "\nAIdit: "
        response = ""
        for token in self.llm.create_completion(
            prompt=prompt,
            echo=False,
            max_tokens=300,
            stream=True,
            stop=["User:", "AIdit:"],
        ):
            token_text = token['choices'][0]['text']
            response += token_text
            if callback:
                callback(token_text)
        self.conversation_history.append({'role': 'AIdit', 'content': response.strip()})
        return response.strip()

    def extract_financial_data(self, text, callback=None):
        prompt = f"{self.EXTRACT_PROMPT}\n{text}"
        output = ""
        for token in self.llm.create_completion(
            prompt=prompt,
            echo=False,
            max_tokens=None,
            stream=True,
            stop=["END"],
        ):
            token_text = token['choices'][0]['text']
            output += token_text
            if callback:
                callback(token_text)
        answer = output.strip()
        try:
            extracted_data = json.loads(answer)
            self.extracted_data = extracted_data
            return extracted_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}\nOutput was: {answer}")

    def chat_with_aidit(self, user_input, callback=None):
        self.conversation_history.append({'role': 'User', 'content': user_input})
        prompt = self.AIDIT_PROMPT + "\n"
        if self.extracted_data:
            prompt += f"Data keuangan yang telah diekstrak:\n{json.dumps(self.extracted_data)}\n"
        for turn in self.conversation_history:
            prompt += f"{turn['role']}: {turn['content']}\n"
        prompt += "AIdit:"

        response = ""
        for token in self.llm.create_completion(
            prompt=prompt,
            echo=False,
            max_tokens=512,
            stream=True,
            stop=["User:", "AIdit:"],
        ):
            token_text = token['choices'][0]['text']
            response += token_text
            if callback:
                callback(token_text)
        response = response.strip()
        self.conversation_history.append({'role': 'AIdit', 'content': response})
        return response

    def regenerate_last_response(self, callback=None):
        if self.conversation_history and self.conversation_history[-1]['role'] == 'AIdit':
            self.conversation_history.pop()
            last_user_input = self.conversation_history[-1]['content']
            return self.chat_with_aidit(last_user_input, callback)
        else:
            return "Tidak ada respons sebelumnya untuk diregenerasi."

    def reset_conversation(self):
        self.conversation_history = []
        self.extracted_data = None
