import threading
import webbrowser
import time

import numpy as np
import pandas as pd
import fitz  # PyMuPDF
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/js", StaticFiles(directory="static/js"), name="js")


def prepare_results_for_json(results):
    if isinstance(results, pd.DataFrame):
        results = results.replace([np.inf, -np.inf], np.nan).fillna(0)
        return results.to_dict(orient='records')
    elif isinstance(results, pd.Series):
        results = results.replace([np.inf, -np.inf], np.nan).fillna(0)
        return results.to_dict()
    elif isinstance(results, dict):
        return {key: prepare_results_for_json(value) for key, value in results.items()}
    else:
        return results


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        with fitz.open(stream=contents, filetype="pdf") as doc:
            text = "".join(page.get_text() for page in doc)

        chatbot = Chatbot()
        financial_data = chatbot.extract_financial_data(text)
        df = pd.DataFrame(financial_data)

        required_columns = [
            "Year",
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
        df = df.reindex(columns=required_columns, fill_value=0)
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0)

        calculator = BeneishMScoreCalculator(df)
        results = calculator.get_results()
        processed_results = prepare_results_for_json(results)

        return JSONResponse(content={"status": "success", "results": processed_results})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)})


@app.get("/")
async def read_index():
    with open("static/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


def open_browser():
    time.sleep(2)  # Tunggu sebentar hingga server siap
    webbrowser.open("http://localhost:1010")


if __name__ == "__main__":
    import uvicorn

    threading.Thread(target=open_browser).start()
    uvicorn.run("main:app", host="localhost", port=1010, reload=True)
