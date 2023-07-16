import ctypes
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from typing import Dict, Any

AUTH_TOKEN = None
AUTH_URL = "https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/alpine:pull"
BASE_REGISTRY_URL = "https://registry.hub.docker.com"


def request(url: str, headers: Dict[str, str] = {}, type: str = "json") -> Any:
    """
    Make an HTTP request and return the response data.

    Args:
        url: The URL to make the request to.
        headers: Optional headers to include in the request.
        type: The expected response type ("json" or "blob").

    Returns:
        The response data based on the specified type.

    Raises:
        urllib.error.URLError: If there was an error making the request.
    """
    req = urllib.request.Request(url, None, headers)

    with urllib.request.urlopen(req) as response:
        if type == "json":
            return json.loads(response.read().decode("utf-8"))
        else:
            return response.read()


def get_headers() -> Dict[str, str]:
    """
    Get the headers for making authenticated requests.
    Ref: https://docs.docker.com/registry/spec/auth/token/

    Returns:
        The headers with the Authorization token.
    """
    global AUTH_TOKEN
    if not AUTH_TOKEN:
        get_auth_token()

    return {"Authorization": f"Bearer {AUTH_TOKEN}"}


def get_auth_token() -> str:
    """
    Get the authentication token for making requests.
    Ref: https://docs.docker.com/registry/spec/auth/token/

    Returns:
        The authentication token.
    """
    global AUTH_TOKEN
    if AUTH_TOKEN:
        return AUTH_TOKEN

    auth_response = request(AUTH_URL)
    AUTH_TOKEN = auth_response["access_token"]

    return auth_response["access_token"]


def pull_image_layer(name: str, layer: str) -> bytes:
    """
    Pull a specific layer of an image from the Docker registry.
    Ref: https://docs.docker.com/registry/spec/api/#pulling-a-layer

    Args:
        name: The name of the image.
        layer: The hash of the layer.

    Returns:
        The layer data as bytes.

    Raises:
        urllib.error.URLError: If there was an error fetching the layer.
    """
    url = f"{BASE_REGISTRY_URL}/v2/library/{name}/blobs/{layer}"

    return request(url, get_headers(), "blob")


def get_image_manifest(name: str, reference: str) -> Dict[str, Any]:
    """
    Get the manifest of a Docker image from the registry.
    Ref: https://docs.docker.com/registry/spec/api/#pulling-an-image-manifest

    Args:
        name: The name of the image.
        reference: The reference of the image (e.g., tag or digest).

    Returns:
        The image manifest as a dictionary.

    Raises:
        urllib.error.URLError: If there was an error fetching the manifest.
    """
    url = f"{BASE_REGISTRY_URL}/v2/library/{name}/manifests/{reference}"

    return request(url, get_headers())


def main():
    """
    Main entry point of the program.
    """
    image_name = sys.argv[2]
    command = sys.argv[3]
    args = sys.argv[4:]

    # Create a temporary directory to store the extracted image layers
    temp_dir = tempfile.TemporaryDirectory()

    manifest = get_image_manifest(image_name, "latest")

    # Extract the corresponding layer blobs from the docker repository
    for layer in manifest["fsLayers"]:
        image_layer_blob = pull_image_layer(image_name, layer["blobSum"])
        with tarfile.open(fileobj=io.BytesIO(image_layer_blob)) as tar:
            tar.extractall(temp_dir.name)

    # Unsharing the PID namespace ensures process isolation within the chroot environment
    # Ref: https://man7.org/linux/man-pages/man7/pid_namespaces.7.html
    CLONE_NEWPID = 0x20000000
    libc = ctypes.CDLL("libc.so.6")
    libc.unshare(CLONE_NEWPID)

    # The chroot command changes the root directory to the extracted image file system,
    # providing an isolated environment for executing the command
    # Ref: https://en.wikipedia.org/wiki/Chroot
    completed_process = subprocess.run(
        ["chroot", temp_dir.name, command, *args],
        capture_output=True,
    )

    sys.stdout.write(completed_process.stdout.decode("utf-8"))
    sys.stderr.write(completed_process.stderr.decode("utf-8"))

    exit(completed_process.returncode)


if __name__ == "__main__":
    main()
