import base64
from google import genai
import logging

logging.basicConfig(level=logging.INFO)

api_key = "AQ.Ab8RN6KQi3py3pRht5onHJrSFOF0QWej0iubZ1zKp1FmM26aJg"
client = genai.Client(api_key=api_key)

try:
    print("Trying generate_images...")
    config = dict(
        number_of_images=1,
        aspect_ratio="1:1",
        output_mime_type="image/jpeg"
    )
    result = client.models.generate_images(
        model="nano-banana-pro-preview",
        prompt="A cute cat",
        config=config
    )
    print("generate_images succeeded!")
except Exception as e:
    print("generate_images failed:", e)

try:
    print("\nTrying generate_content...")
    response = client.models.generate_content(
        model="nano-banana-pro-preview",
        contents="A cute cat",
    )
    print("generate_content succeeded!")
    print("Response parts:", response.candidates[0].content.parts)
    
    # Try to extract image
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            print("Found inline data!")
            # print first 20 bytes
            print(part.inline_data.data[:20])
except Exception as e:
    print("generate_content failed:", e)
