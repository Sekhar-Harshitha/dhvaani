import os
import io
import urllib.request
from PIL import Image

OUT_DIR = os.path.join("static", "assets", "images")
os.makedirs(OUT_DIR, exist_ok=True)

# Curated Unsplash photos for Indian civic / public-service contexts (Unsplash license)
SOURCES = [
    {
        "filename": "farmer-community.webp",
        "url": "https://images.unsplash.com/photo-1595974482597-4b8da8879bc5?auto=format&fit=crop&w=800&q=80",
        "fallback_url": "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=800&q=80",
        "alt": "Indian farmer in agricultural field receiving scheme assistance",
        "author": "Unsplash Community",
        "license": "Unsplash Free License"
    },
    {
        "filename": "citizen-support.webp",
        "url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=800&q=80",
        "fallback_url": "https://images.unsplash.com/photo-1509099836639-18ba1795216d?auto=format&fit=crop&w=800&q=80",
        "alt": "Indian woman and family accessing public welfare services",
        "author": "Unsplash Community",
        "license": "Unsplash Free License"
    },
    {
        "filename": "community-health.webp",
        "url": "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?auto=format&fit=crop&w=800&q=80",
        "fallback_url": "https://images.unsplash.com/photo-1576091160550-2173dba999ef?auto=format&fit=crop&w=800&q=80",
        "alt": "Healthcare professional providing medical support in community clinic",
        "author": "Unsplash Community",
        "license": "Unsplash Free License"
    },
    {
        "filename": "civic-infrastructure.webp",
        "url": "https://images.unsplash.com/photo-1570125909232-eb263c188f7e?auto=format&fit=crop&w=800&q=80",
        "fallback_url": "https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=800&q=80",
        "alt": "Civic urban infrastructure, clean roads and public streetlighting",
        "author": "Unsplash Community",
        "license": "Unsplash Free License"
    },
    {
        "filename": "public-service.webp",
        "url": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=800&q=80",
        "fallback_url": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=800&q=80",
        "alt": "Young students discovering educational scholarships and civic opportunities",
        "author": "Unsplash Community",
        "license": "Unsplash Free License"
    }
]

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

for item in SOURCES:
    filepath = os.path.join(OUT_DIR, item["filename"])
    success = False
    for url in [item["url"], item.get("fallback_url")]:
        if not url:
            continue
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                img_data = response.read()
                img = Image.open(io.BytesIO(img_data))
                img = img.convert("RGB")
                img.save(filepath, "WEBP", quality=82, method=6)
                print(f"[OK] Downloaded and converted {item['filename']} ({os.path.getsize(filepath)} bytes)")
                success = True
                break
        except Exception as e:
            print(f"Failed {url}: {e}")
    if not success:
        print(f"[ERROR] Could not download {item['filename']}")
