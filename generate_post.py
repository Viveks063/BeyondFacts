from google import genai
from dotenv import load_dotenv
import os
import requests
import urllib.parse
from PIL import Image
from io import BytesIO

load_dotenv(override=True)

# 1. Generate text post using Gemini 2.5 Flash
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

text_prompt = """
Create an Instagram post about AI startups.

Return:
Hook
Caption
Hashtags
Image Prompt (A detailed prompt to generate an image for this post)
"""

print("--- Generating Post Text & Image Prompt ---")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=text_prompt,
)

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

print(response.text)

# 2. Extract or use an image prompt for Phase 4: Image Generation
image_prompt = "Futuristic AI startup team working in a modern glowing high tech office, photorealistic, 4k"

# 3. Generate and save the image
print("\n--- Phase 4: Generating Image ---")
encoded_prompt = urllib.parse.quote(image_prompt)
image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1084&height=1084&nologo=true"

headers = {"User-Agent": "Mozilla/5.0"}
img_res = requests.get(image_url, headers=headers)

if img_res.status_code == 200:
    image_filename = "post_image.jpg"
    img = Image.open(BytesIO(img_res.content))
    img.save(image_filename)
    print(f"Success! Image generated and saved to '{image_filename}' ({img.size[0]}x{img.size[1]}px)")
else:
    print(f"Failed to generate image. HTTP Status: {img_res.status_code}")