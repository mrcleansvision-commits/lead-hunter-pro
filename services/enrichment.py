import httpx
from bs4 import BeautifulSoup
import asyncio
import re
import urllib.parse
import random

async def find_owner_info(business_name: str, location: str) -> dict:
    """
    Searches for owner information using lightweight HTTP requests (Cloud Safe).
    """
    info = {
        "owner_name": None,
        "owner_contact": None,
        "enrichment_status": "Not Found"
    }
    
    # Random User Agents to avoid immediate blocking
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    ]
    
    queries = [
        f'{business_name} {location} owner',
        f'{business_name} {location} contact email'
    ]
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        found_name = None
        found_contact = None
        
        for q in queries:
            if found_name and found_contact:
                break
                
            print(f"Enrichment search (Cloud): {q}")
            try:
                # Use DuckDuckGo HTML version (easier to scrape)
                encoded_q = urllib.parse.quote(q)
                url = f"https://html.duckduckgo.com/html/?q={encoded_q}"
                
                headers = {"User-Agent": random.choice(user_agents)}
                resp = await client.get(url, headers=headers)
                
                if resp.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(resp.text, 'html.parser')
                results = soup.select(".result__snippet")
                
                for r in results:
                    text = r.get_text()
                    
                    # Same heuristics as before
                    if not found_name:
                        match = re.search(r'(?:Owner|CEO|President|Founder)[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)', text)
                        if match:
                            found_name = match.group(1)
                            
                    if not found_contact:
                        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
                        if email_match:
                            found_contact = email_match.group(0)
                        
            except Exception as e:
                print(f"Enrichment error on query {q}: {e}")
                
        if found_name:
            info["owner_name"] = found_name
            info["enrichment_status"] = "Found"
        
        if found_contact:
            info["owner_contact"] = found_contact
            
    return info
