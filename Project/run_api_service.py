"""Entry point 5: the BreachWatch AI API service that the dashboard talks to.

Run with:  python run_api_service.py
"""

import uvicorn

from api.routes import service_application
from config import config


def main():
    """Serve the API on the host and port set in config."""
    print(f"{config.API_TITLE} at {config.API_BASE_URL}  (docs: {config.API_BASE_URL}/docs)")
    uvicorn.run(service_application, host=config.API_HOST, port=config.API_PORT)


if __name__ == "__main__":
    main()
