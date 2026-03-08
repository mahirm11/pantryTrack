from google import genai
from PIL import Image
from pydantic import BaseModel, Field
from typing import List
import io

client = genai.Client(api_key = "AIzaSyD-25YAB4o5kzAaEUadaAUloxzTVzrZzM4")

class Expiration(BaseModel):
    freezer : int = Field(description="how long can this food item last when stored in a freezer")
    fridge : int = Field(description="how long can this food item last when stored in a fridge")
    pantry : int = Field(description="how long can this food item last when stored in a pantry")
    indoors : int = Field(description="how long can this food item last when stored in outside a pantry, fridge, or freezer, but still inside a room")

class Foods(BaseModel):
    name: str = Field(description="name of food")
    qty : int = Field(description="quantity of food item")
    expiration: Expiration

class Everything(BaseModel):
    data: List[Foods]

def image_scan(image_bytes: bytes):
    image = Image.open(io.BytesIO(image_bytes))
    image.thumbnail([1024,1024], Image.Resampling.LANCZOS)
    return image

def parse_receipt(image_bytes: bytes) -> dict:
    im = image_scan(image_bytes)

    prompt = "Take every food item in this receipt and create multiple dictionaries of each foods"

    response = client.models.generate_content(
        model = "gemini-3-flash-preview", contents = [im, prompt], config = {"response_mime_type": "application/json","response_json_schema": Everything.model_json_schema()}
    )

    output = Everything.model_validate_json(response.text).model_dump()

    return output