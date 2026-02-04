from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import random
import os

# Import services (to be created)
# from services.maps_scraper import search_businesses
# from services.enrichment import find_owner_info

app = FastAPI(title="Lead Finder & Enrichment Tool")

# Ensure static directories exist for Cloud Deployment
os.makedirs("static/generated", exist_ok=True)

# Mount static files (CSS, JS, Images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates for the frontend
templates = Jinja2Templates(directory="templates")

# --- Data Models ---
class SearchRequest(BaseModel):
    niche: str
    location: str
    api_key: str
    deep_scan: bool = False # Default to False

class Business(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    has_website: bool
    owner_name: Optional[str] = None
    owner_contact: Optional[str] = None
    source: str = "Google Maps"

@app.get("/")
async def read_root(request: Request):
    """Render the dashboard."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/search")
async def search_leads(request: SearchRequest):
    """
    Search for businesses using Google API.
    """
    print(f"Searching for {request.niche} in {request.location} (Deep Scan: {request.deep_scan})")
    
    if not request.api_key:
         return {"status": "error", "message": "API Key is required"}

    # Real implementation
    try:
        from services.maps_scraper import search_google_maps
        # Fetch results with deep_scan option
        raw_results = await search_google_maps(
            request.niche, 
            request.location, 
            max_results=10000, 
            api_key=request.api_key,
            deep_scan=request.deep_scan
        )
        
        # Format results
        results = []
        for r in raw_results:
            results.append({
                "name": r["name"],
                "address": r.get("address", "N/A"), 
                "phone": r.get("phone", "N/A"),
                "website": r.get("website"),
                "has_website": r["has_website"],
                "owner_name": None,
                "owner_contact": None
            })
            
        # Filter for no website
        filtered = [b for b in results if not b['has_website']]
        
        return {
            "status": "success", 
            "results": filtered, 
            "total_found": len(filtered),
            "total_scanned": len(results)
        }
        
    except Exception as e:
        print(f"Search error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/enrich")
async def enrich_lead(business: Business):
    """
    Find owner info for a specific business.
    """
    try:
        from services.enrichment import find_owner_info
        # Use business name and address (or location inferred from address)
        # We'll just pass the address as location context
        
        info = await find_owner_info(business.name, business.address or "")
        
        return info
    except Exception as e:
        print(f"Enrichment failed: {e}")
        return {
            "owner_name": None,
            "owner_contact": None,
            "enrichment_status": "Error"
        }

@app.post("/api/generate-site")
async def generate_site(request: Request):
    data = await request.json()
    
    business_name = data.get("business_name")
    niche = data.get("niche")
    location = data.get("location")
    ai_api_key = data.get("ai_api_key")
    provider = data.get("provider", "openai") # or gemini
    
    if not ai_api_key:
        return JSONResponse({"status": "error", "message": "AI API Key is required"}, status_code=400)
        
    print(f"Generating site for {business_name} using {provider}...")
    
    try:
        from services.site_generator import generate_landing_page
        html_content = await generate_landing_page(business_name, niche, location, ai_api_key, provider)
        
        # Save to a temporary file or return directly
        # We'll save it to static/generated/{safe_name}.html so we can preview it
        safe_name = "".join([c for c in business_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_').lower()
        filename = f"{safe_name}.html"
        os.makedirs("static/generated", exist_ok=True)
        
        file_path = f"static/generated/{filename}"
        with open(file_path, "w") as f:
            f.write(html_content)
            
        return {"status": "success", "preview_url": f"/static/generated/{filename}"}

    except Exception as e:
        print(f"Generation error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    # Use 0.0.0.0 to enable access from other devices if needed, but localhost is fine for now
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
