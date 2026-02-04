import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
from pydantic import BaseModel
from typing import Optional

# Import our services
from services.maps_scraper import search_google_maps
from services.enrichment import find_owner_info
from services.site_generator import generate_landing_page

app = FastAPI()

# Ensure static directories exist for Cloud Deployment
os.makedirs("static/generated", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Data Models
class SearchRequest(BaseModel):
    niche: str
    location: str
    api_key: Optional[str] = None
    deep_scan: bool = True

class EnrichRequest(BaseModel):
    business_name: str
    location: str

class GenerateSiteRequest(BaseModel):
    business_name: str
    niche: str
    location: str
    api_key: Optional[str] = None
    provider: str = "openai"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/search")
async def search_leads(request: SearchRequest):
    print(f"Searching for {request.niche} in {request.location}...")
    
    # 1. Scrape Google Maps
    # We pass a very high limit now, letting the scraper decide when to stop
    raw_results = await search_google_maps(
        request.niche, 
        request.location, 
        max_results=10000, 
        api_key=request.api_key,
        deep_scan=request.deep_scan
    )
    
    return {"results": raw_results, "count": len(raw_results)}

@app.post("/api/enrich")
async def enrich_lead(request: EnrichRequest):
    print(f"Enriching: {request.business_name}...")
    info = await find_owner_info(request.business_name, request.location)
    return info

@app.post("/api/generate-site")
async def generate_site(request: GenerateSiteRequest):
    print(f"Generating site for: {request.business_name}")
    
    html_content = await generate_landing_page(
        request.business_name,
        request.niche,
        request.location,
        request.api_key,
        request.provider
    )
    
    # Save to static/generated for preview
    filename = f"site_{request.business_name.replace(' ', '_')}.html"
    filepath = f"static/generated/{filename}"
    
    with open(filepath, "w") as f:
        f.write(html_content)
        
    return {"status": "success", "preview_url": f"/static/generated/{filename}"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
