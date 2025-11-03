# Telex Bank Agent

This project is a Python-based agent that retrieves bank alert emails from an IMAP inbox, matches them to a list of transactions, and sends notifications via Telex.

## Features

-   **IMAP Email Polling:** Periodically checks an email inbox for new bank alerts.
-   **Transaction Matching:** Matches emails to transactions with a configurable accuracy threshold.
-   **Telex Integration:** Sends notifications with the match results.
-   **Gemini Integration:** Uses Google Gemini for intelligent email parsing.
-   **FastAPI Backend:** Provides a robust API for interaction and monitoring.

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py         # FastAPI application
│   ├── config.py       # Configuration management
│   ├── db.py           # Database setup
│   ├── models.py       # Database models
│   ├── schemas.py      # Pydantic schemas
│   ├── email_reader.py # IMAP email reader
│   ├── email_parser.py # Email parsing logic
│   ├── poller.py       # Transaction polling
│   ├── matcher.py      # Transaction matching logic
│   ├── telex_client.py # Telex client
│   └── gemini_client.py# Gemini client
├── tests/
│   ├── test_matcher.py
│   └── test_end_to_end.py
├── .env                # Environment variables
├── .gitignore          # Git ignore file
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd telex-bank-agent
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure your environment:**
    -   Rename the `.env.example` file to `.env`.
    -   Open the `.env` file and fill in your credentials for Mailtrap, Telex, and Google Gemini.

## Running the Application

To run the application, use the following command:

```bash
uvicorn app.main:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

## How to Connect to Telex

1.  **Get your Telex Webhook URL and Channel ID:**
    -   Log in to your Telex account.
    -   Navigate to the channel you want to use for notifications.
    -   In the channel settings, find the "Integrations" or "Webhooks" section.
    -   Create a new webhook and copy the URL.
    -   The Channel ID is usually found in the channel's settings or URL.

2.  **Update your `.env` file:**
    -   Paste the webhook URL into the `TELEX_WEBHOOK_URL` field.
    -   Paste the channel ID into the `TELEX_CHANNEL_ID` field.

## How to Test the Application

1.  **Run the tests:**
    -   The project is set up with `pytest`. To run the tests, use the following command:
        ```bash
        pytest
        ```

2.  **Manual Testing:**
    -   **Send a test email:** Send a sample bank alert email to your Mailtrap inbox.
    -   **Check the logs:** The application will log the email processing and matching results to the console.
    -   **Check Telex:** If the match is successful, you should receive a notification in your configured Telex channel.
    -   **Use the API:** You can interact with the API at `http://127.0.0.1:8000/docs`.

## API Endpoints

-   `GET /`: Returns the service status.
-   `POST /transactions`: Adds a new transaction.
-   `POST /emails`: Ingests a new email.
-   `GET /admin/match_runs`: Returns a list of all match runs.
