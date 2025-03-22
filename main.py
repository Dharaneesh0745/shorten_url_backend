from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
from Schema.Shorten_URL import Url
from prisma import Prisma
from dotenv import load_dotenv
import hashlib
import base64

load_dotenv()
app = FastAPI()
db = Prisma()

origins = ["http://localhost:5173", "https://url-shorten.codesynth.xyz"]

cors_middleware: Any = CORSMiddleware
app.add_middleware(
    cors_middleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with db:
        await db.connect()

@app.on_event("shutdown")
async def shutdown():
    async with db:
        await db.disconnect()

@app.get("/")
async def root():
    return {"message": "API is working!"}

def hash_shorten_url(url: str) -> str:
    hash_object = hashlib.sha256(url.encode())
    short_hash = base64.urlsafe_b64encode(hash_object.digest())[:7].decode()
    return short_hash

@app.post("/shorten-url")
async def shorten_url(url: Url) -> dict:
    record = await db.urls.find_unique(where={"original_url": url.url})

    if record:
        return {
            "success": False,
            "message": "Shortened URL already exists",
            "url": f"https://cs.xyz/{record.shorten_url}"
        }

    hash_code = hash_shorten_url(url.url)

    new_record = await db.urls.create(
        data={
            "original_url": url.url,
            "shorten_url": hash_code,
        }
    )

    return {
        "success": True,
        "message": "Short URL created!",
        "url": f"https://cs.xyz/{new_record.shorten_url}"
    }

@app.post("/redirect-original-url")
async def redirect_original_url(url: Url) -> dict:

    format_url = url.url[15:]

    record = await db.urls.find_unique(where={"shorten_url": format_url})

    if record:
        await db.urls.update(
            where={"shorten_url": url.url},
            data={"no_of_visits": record.no_of_visits + 1}
        )

        return {
            "success": True,
            "message": "Shorten URL found!",
            "url": f"{record.original_url}"
        }

    return {
        "success": False,
        "message": "URL mapping not found, create a new shorten URL!",
    }