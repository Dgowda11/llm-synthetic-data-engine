
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
        self.organization_url = _validate_organization_url(organization_url)
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


def _validate_organization_url(organization_url: str) -> str:
    value = organization_url.strip().rstrip("/")
    if not value:
        raise ValueError("Azure DevOps organization URL cannot be empty.")

    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Azure DevOps organization URL must be a valid HTTPS URL.")

    path_parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc.casefold() == "dev.azure.com":
        if len(path_parts) != 1:
            raise ValueError(
                "AZURE_DEVOPS_ORG must be the organization root, for example "
                "https://dev.azure.com/my-organization, without a project path."
            )
    elif path_parts:
        raise ValueError(
            "Legacy Azure DevOps organization URLs must not include a project path."
        )
    return value
    