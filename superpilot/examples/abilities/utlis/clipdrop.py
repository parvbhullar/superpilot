import time
import requests

API_HOST = "https://clipdrop-api.co/text-to-image/v1"


def generate_image_with_clip_drop(body, headers, api_host=API_HOST) -> str:
    """Generate an image with ClipDrop.
    Args:
        body (dict): The body of the request
        headers (dict): The headers of the request
        api_host (str): The host of the API
        engine_id (str): The ID of the engine to use. Defaults to ENGINE_ID.
    """
    # Create a session and set the basic auth if needed
    session = requests.Session()
    session.headers.update(headers)
    clip_drop_url = api_host
    t1 = time.time()
    print(f"Sending request to {clip_drop_url}", t1)
    response = session.post(clip_drop_url, files=body, headers=headers)
    t2 = time.time()
    print(f"Response Received", t2)
    print(f"Total time: {round(t2 - t1, 4)} Secs")
    return response.content, response.status_code == 200
