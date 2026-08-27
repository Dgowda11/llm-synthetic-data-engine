
from typing import Any
from urllib.parse import urlparse

import requests
from requests.auth import HTTPBasicAuth


class AzureDevOpsClient:
    def __init__(
        self,
        organization_url: str,
        pat: str,
        timeout: float = 30,
    ) -> None:
        self.organization_url = organization_url.strip().rstrip("/")
        if not self.organization_url:
            raise ValueError("Azure DevOps organization URL cannot be empty.")
        if not pat.strip():
            raise ValueError("Azure DevOps PAT cannot be empty.")
        if timeout <= 0:
            raise ValueError("Timeout must be greater than zero.")

        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth("", pat.strip())
        self.session.headers.update({"Accept": "application/json"})

    def request(
        self,
        method: str,
        path_or_url: str,
        *,
        params: dict[str, str] | None = None,
        json_body: dict[str, object] | list[dict[str, object]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = (
            path_or_url
            if path_or_url.startswith(("https://", "http://"))
            else f"{self.organization_url}/{path_or_url.lstrip('/')}"
        )
        if path_or_url.startswith(("https://", "http://")):
            organization = urlparse(self.organization_url)
            target = urlparse(path_or_url)
            if (
                target.scheme != organization.scheme
                or target.netloc != organization.netloc
                or not target.path.startswith(organization.path.rstrip("/") + "/")
            ):
                raise ValueError(
                    "Refusing to send Azure credentials outside the configured organization."
                )

        try:
            response = self.session.request(
                method,
                url,
                params=params,
                json=json_body,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.Timeout as error:
            raise RuntimeError("Azure DevOps request timed out.") from error
        except requests.ConnectionError as error:
            raise RuntimeError("Could not connect to Azure DevOps.") from error
        except requests.HTTPError as error:
            status_code = (
                error.response.status_code
                if error.response is not None
                else "unknown"
            )
            raise RuntimeError(
                f"Azure DevOps request failed with status {status_code}."
            ) from error

        try:
            result = response.json()
        except requests.JSONDecodeError as error:
            raise RuntimeError("Azure DevOps returned invalid JSON.") from error

        if not isinstance(result, dict):
            raise RuntimeError("Azure DevOps returned an unexpected response shape.")
        return result
    