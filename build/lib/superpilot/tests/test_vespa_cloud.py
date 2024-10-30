from vespa.application import Vespa
import os

token_endpoint = "https://vespa-app.cloud/"
app = Vespa(
    url=token_endpoint, vespa_cloud_secret_token=os.getenv("VESPA_CLOUD_SECRET_TOKEN", "")
)
app.get_application_status()