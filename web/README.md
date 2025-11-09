# Ganymede Web UI

Simple TUI-style web interface for the Ganymede notebook conversion API using FastAPI and HTMX.

## Setup

1. Install dependencies:
```bash
cd web
uv sync
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `API_URL`: URL of the Ganymede API (default: http://localhost:8000)
- `S3_ENDPOINT_URL`: S3-compatible storage endpoint
- `S3_ACCESS_KEY_ID`: S3 access key
- `S3_SECRET_ACCESS_KEY`: S3 secret key
- `S3_BUCKET_NAME`: S3 bucket name
- `S3_REGION`: S3 region (default: us-east-1)

Optional:
- `MAX_FILE_SIZE_MB`: Maximum file size in MB (default: 50)

## Running

Make sure the API server is running first, then:

```bash
cd web
uv run uvicorn main:app --reload --port 8001
```

The web UI will be available at http://localhost:8001

## Usage

1. Open http://localhost:8001 in your browser
2. Select a `.ipynb` or `.zip` file (max 50MB)
3. Click "Convert"
4. Wait for the conversion to complete (a spinner will show progress)
5. Download the resulting PDF

## Architecture

- **FastAPI**: Web server and API endpoints
- **HTMX**: Dynamic updates without full page reloads
- **Jinja2**: HTML templating
- Server-side file upload to S3/Backblaze
- Automatic polling for job status updates
- PDF download proxied through the server

## Files

- `main.py`: FastAPI application with upload, status, and download endpoints
- `templates/index.html`: Main UI page with HTMX
- `static/style.css`: TUI-style CSS (man-page aesthetic)
- `.env.example`: Configuration template
