import threading
import webbrowser
import time

import numpy as np
import pandas as pd
import fitz  # PyMuPDF
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import asyncio

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


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    chatbot = Chatbot()
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    try:
        def send_token(token_text):
            asyncio.run_coroutine_threadsafe(websocket.send_text(token_text), loop)

        await asyncio.to_thread(chatbot.get_initial_greeting, callback=send_token)
        await websocket.send_json({"status": "completed"})

        while True:
            data = await websocket.receive_json()
            command = data.get('command')

            if command == 'upload_file':
                pdf_bytes = bytes(data['pdf_bytes'])
                with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                    text = "".join(page.get_text() for page in doc)
                def send_extract_progress(token_text):
                    asyncio.run_coroutine_threadsafe(websocket.send_text(token_text), loop)

                try:
                    financial_data = await asyncio.to_thread(
                        chatbot.extract_financial_data, text, callback=send_extract_progress
                    )
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

                    ai_message = "Data keuangan Anda telah berhasil diekstrak dan dianalisis. Berikut adalah hasil analisisnya."
                    chatbot.conversation_history.append({'role': 'AIdit', 'content': ai_message})

                    await websocket.send_json({"status": "file_processed", "results": processed_results})
                except Exception as e:
                    await websocket.send_json({"error": str(e)})
                finally:
                    stop_event.clear()
            elif command == 'user_message':
                user_input = data['message']

                def send_chat_token(token_text):
                    if not stop_event.is_set():
                        asyncio.run_coroutine_threadsafe(websocket.send_text(token_text), loop)

                response_task = asyncio.create_task(
                    asyncio.to_thread(
                        chatbot.chat_with_aidit, user_input, callback=send_chat_token
                    )
                )
                await response_task
                await websocket.send_json({"status": "completed"})
                stop_event.clear()
            elif command == 'regenerate':
                def send_regen_token(token_text):
                    asyncio.run_coroutine_threadsafe(websocket.send_text(token_text), loop)

                response = await asyncio.to_thread(chatbot.regenerate_last_response, callback=send_regen_token)
                await websocket.send_json({"status": "completed"})
                stop_event.clear()
            elif command == 'reset':
                chatbot.reset_conversation()
                await websocket.send_json({"status": "reset_completed"})
                stop_event.clear()
            elif command == 'stop':
                stop_event.set()
                await websocket.send_json({"status": "stopped"})
            elif command == 'delete_message':
                message_index = data.get('message_index')
                if 0 <= message_index < len(chatbot.conversation_history):
                    chatbot.conversation_history.pop(message_index)
                    await websocket.send_json({"status": "message_deleted"})
                else:
                    await websocket.send_json({"error": "Invalid message index"})
                stop_event.clear()
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        await websocket.send_json({"error": str(e)})


@app.get("/")
async def read_index():
    with open("static/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:1010")


if __name__ == "__main__":
    import uvicorn

    threading.Thread(target=open_browser).start()
    uvicorn.run("main:app", host="localhost", port=1010, reload=True)
