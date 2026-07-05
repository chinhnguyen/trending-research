"""Run the Willbe Trends API server."""

import uvicorn

from willbe_trends.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "willbe_trends.api.app:app",
        host=settings.willbe_api_host,
        port=settings.willbe_api_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
