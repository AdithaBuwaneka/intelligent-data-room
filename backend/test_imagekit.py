import base64
from imagekitio import ImageKit

# Test ImageKit connection
ik = ImageKit(
    public_key="public_+E8Y/QRscbqHrn5Rs84d9nLTntY=",
    private_key="private_EyD4JzRQM70nHQPQormqR27HzRM=",
    url_endpoint="https://ik.imagekit.io/Aditha",
)

# Create simple test content
content = b"Name,Sales\nTest,100"
encoded = base64.b64encode(content).decode('utf-8')

try:
    result = ik.upload_file(
        file=encoded,
        file_name="test.csv",
        options={
            "folder": "/data-room",
            "is_private_file": False,
            "use_unique_file_name": True,
        },
    )
    print("Result:", result)
    print("URL:", result.url if hasattr(result, 'url') else "No URL")
    print("Error:", result.error if hasattr(result, 'error') else "No error")
except Exception as e:
    print("Exception:", e)
