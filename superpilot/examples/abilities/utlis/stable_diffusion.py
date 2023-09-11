import json
import time
import requests

ENGINE_ID = "stable-diffusion-512-v2-1"
API_HOST = "https://api.stability.ai"


# "https://api.stability.ai/v1/generation/stable-diffusion-512-v2-1/text-to-image"
def generate_image_with_sd(
    body, headers, service_type="text-to-image", api_host=API_HOST, engine_id=ENGINE_ID
) -> str:
    """Generate an image with Stable Diffusion.
    Args:
        body (dict): The body of the request
        headers (dict): The headers of the request
        api_host (str): The host of the API
        engine_id (str): The ID of the engine to use. Defaults to ENGINE_ID.
    """
    # Create a session and set the basic auth if needed
    session = requests.Session()
    session.headers.update(headers)
    session.headers.update(
        {"Content-Type": "application/json", "Accept": "application/json"}
    )
    sd_url = f"{api_host}/v1/generation/{engine_id}/{service_type}"
    t1 = time.time()
    print(f"Sending request to {sd_url}", t1)
    response = session.post(sd_url, data=json.dumps(body), headers=headers)
    t2 = time.time()
    print(f"Response Received", t2)
    print(f"Total time: {round(t2 - t1, 4)} Secs")
    return response.json(), response.status_code == 200
