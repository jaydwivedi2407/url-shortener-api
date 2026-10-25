
# URL Shortener API

A simple URL Shortener API built using Python, FastAPI, and SQLite. It allows users to create short links, redirect to original URLs, track link statistics, and set expiration dates.

## Features

- Create short URLs with automatically generated codes.
- Create custom aliases for short links.
- Redirect short links to their original URLs.
- Track click counts and the last clicked time.
- Set expiration dates for short links.
- Validate URLs and expiration dates.
- Reject duplicate aliases.
- Return appropriate HTTP error codes for missing and expired links.
- Store link information in an SQLite database.

## Technologies Used

- Python 3.12
- FastAPI
- SQLite
- Uvicorn
- Pytest
- HTTPX

## Setup and Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd url-shortner
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
python -m pip install fastapi "uvicorn[standard]" pytest httpx
```

### 5. Start the API server

```bash
python -m uvicorn main:app --reload
```

The API will be available at:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Check API status |
| POST | `/links` | Create a short link |
| GET | `/{code}` | Redirect to the original URL |
| GET | `/{code}/stats` | Get link statistics |

## Create a Short Link

Send a POST request to `/links` with a JSON body:

```json
{
  "url": "https://example.com",
  "alias": "myexample"
}
```

The alias is optional. An expiration date can also be provided using `expires_at`.

Example response:

```json
{
  "code": "myexample",
  "short_url": "http://127.0.0.1:8000/myexample",
  "original_url": "https://example.com/",
  "expires_at": null
}
```

## Redirect to the Original URL

Open the generated short URL in a browser:

http://127.0.0.1:8000/myexample

The API redirects the request to the original URL.

## Link Statistics

Send a GET request to:

`/myexample/stats`

The response includes the original URL, click count, last clicked time, and expiration date.

## Error Handling

| Status Code | Meaning |
|---|---|
| 404 | Short link not found |
| 409 | Alias or short code already exists |
| 410 | Short link has expired |
| 422 | Invalid URL or expiration date |

## Running Tests

Run the automated test suite:

```bash
python -m pytest -v
```

The test suite covers API status, link creation, duplicate aliases, unknown codes, invalid URLs, past expiration dates, and expired links.

## Database

The application uses SQLite and automatically creates the `urls.db` database when the API starts. The database file is excluded from version control.

## Author

Developed as a URL Shortener API project.
