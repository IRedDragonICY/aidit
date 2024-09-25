# main.py
import pandas as pd
import fitz
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import math
import numpy as np

from lib.Chatbot import Chatbot
from lib.audit.Beneish import BeneishMScoreCalculator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def remove_nan_and_inf(obj):
    if isinstance(obj, dict):
        return {k: remove_nan_and_inf(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [remove_nan_and_inf(x) for x in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        else:
            return obj
    else:
        return obj

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        with fitz.open(stream=contents, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()

        chatbot = Chatbot()
        financial_data = chatbot.extract_financial_data(text)
        df = pd.DataFrame(financial_data)

        required_columns = ["Year", "Net Receivables", "Sales", "Cost of Goods Sold",
                            "Current Assets", "PPE", "Net PPE", "Securities", "Total Assets",
                            "Depreciation Expense", "SG&A Expenses", "Total Debt",
                            "Income from Continuing Operations", "Cash from Operations"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = 0

        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.fillna(0, inplace=True)

        calculator = BeneishMScoreCalculator(df)

        results = calculator.get_results()

        if isinstance(results, pd.DataFrame):
            results = results.to_dict(orient='records')
        elif isinstance(results, pd.Series):
            results = results.to_dict()
        elif isinstance(results, dict):
            for key, value in results.items():
                if isinstance(value, (pd.DataFrame, pd.Series)):
                    results[key] = value.to_dict(orient='records' if isinstance(value, pd.DataFrame) else 'dict')

        results = remove_nan_and_inf(results)

        return JSONResponse(content={"status": "success", "results": results})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)})


@app.get("/")
async def read_index():
    with open("static/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="localhost", port=1010, reload=True)