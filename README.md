
# AIdit: AI-Based Audit Assistant

AIdit is an AI-based audit assistant designed to help users with audit-related tasks, including extracting and processing financial data from PDF documents. This application provides a web interface to interact with the AI model, which can analyze financial statements using the Beneish M-Score formula to detect potential earnings manipulation.

## Features

- **Chat Interface**: A responsive web chat interface that allows users to communicate with AIdit, ask questions, or upload PDF files for financial analysis.
- **PDF Data Extraction**: Extracts key financial data from uploaded PDF files and formats it into a structured JSON format.
- **Beneish M-Score Calculation**: Uses the extracted data to calculate the Beneish M-Score, providing insights into potential earnings manipulation.
- **Multi-Turn Conversations**: Supports ongoing conversations where users can ask multiple questions and receive concise answers.

## Project Structure

```
├── static/
│   ├── css/
│   │   └── style.css   # Styles for the web interface
│   ├── js/
│   │   └── scripts.js  # JavaScript for handling WebSocket and UI interactions
│   └── index.html      # Main HTML file for the web interface
├── Beneish.py           # Beneish M-Score calculation logic
├── Chatbot.py           # Chatbot logic for interacting with AI and handling PDF data extraction
├── main.py              # FastAPI server and WebSocket implementation
└── README.md            # Project documentation
```

### Key Components

- **Chat Interface**: Built using HTML, CSS (Bootstrap), and JavaScript (jQuery), it allows users to send messages or upload files. Real-time communication is handled using WebSocket.
- **Backend API**: Powered by FastAPI, this server manages WebSocket connections, file uploads, and interactions with the chatbot.
- **Beneish M-Score Calculation**: The `Beneish.py` module implements the calculation of the Beneish M-Score, used for detecting potential earnings manipulation based on extracted financial data.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/audit-assistant.git
   cd audit-assistant
   ```

2. **Install dependencies**:
   Ensure you have Python 3.8+ installed, then install the necessary dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

4. **Access the web interface**:
   Open your browser and go to:
   ```
   http://localhost:1010
   ```

## Usage

1. **Chatting with AIdit**: You can type messages directly into the chat input to ask audit-related questions.
2. **Uploading Files**: Upload a PDF document containing financial data for AIdit to analyze. Once uploaded, AIdit will process the document and provide a Beneish M-Score analysis.
3. **Results**: After processing, the results will be displayed in JSON format, including the Beneish M-Score components and classification (Unlikely, Possible, Likely).

