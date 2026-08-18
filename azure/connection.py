


class AzureDevOpsClient:
    def __init__(self, organization_url: str, pat: str) -> None:
        self.organization_url = organization_url
        self.pat = pat
    