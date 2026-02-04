import googlemaps
import time
import csv
import os
import asyncio
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

async def search_google_maps(niche: str, location: str, max_results: int = 60, api_key: str = None, deep_scan: bool = False) -> List[Dict]:
    """
    Searches Google Places API for businesses.
    Uses asyncio to run multiple region queries IN PARALLEL to avoid server timeouts.
    """
    if not api_key:
        raise ValueError("Google API Key is required")

    # Initialize client (This client is thread-safe)
    gmaps = googlemaps.Client(key=api_key)
    
    # Define queries
    queries = [f"{niche} in {location}"]
    if deep_scan:
        try:
            from services.cities import US_STATES_CITIES
        except ImportError:
            print("Warning: services.cities not found. State Mode disabled.")
            US_STATES_CITIES = {} 
            
        loc_lower = location.lower().strip()
        
        # Check if input is a state
        if loc_lower in US_STATES_CITIES:
            print(f"State Mode Activated for: {location.title()}")
            target_cities = US_STATES_CITIES[loc_lower]
            for city in target_cities:
                queries.append(f"{niche} in {city}, {location}")
        else:
            print(f"Deep Scan Enabled: Generating 8-Point Grid queries for {location}")
            directions = [
                "North", "North East", "East", "South East", 
                "South", "South West", "West", "North West",
                "Central", "Downtown"
            ]
            for direction in directions:
                queries.append(f"{niche} in {direction} {location}")
            
    all_results = {} # place_id -> result_dict to deduplicate
    
    # --- PARALLEL EXECUTION ENGINE ---
    print(f"Starting Parallel Search for {len(queries)} queries...")
    loop = asyncio.get_running_loop()
    
    # We use a ThreadPoolExecutor because googlemaps-python is valid synchronous code
    # This allows us to run 10+ HTTP requests at the same time
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for query in queries:
            # Schedule each query to run in a separate thread
            futures.append(
                loop.run_in_executor(executor, _execute_query, gmaps, query, 60)
            )
        
        # Wait for all to finish (or timeout)
        # We gather all results
        results_list = await asyncio.gather(*futures, return_exceptions=True)
        
    # Process results
    for i, res in enumerate(results_list):
        if isinstance(res, Exception):
            print(f"Query {queries[i]} failed: {res}")
            continue
            
        # res is a list of dicts
        for business in res:
            pid = business['place_id']
            if pid not in all_results:
                all_results[pid] = business
                
    print(f"Search Complete. Found {len(all_results)} unique businesses.")
    return list(all_results.values())

def _execute_query(gmaps, query_text, max_per_query=60):
    """
    Blocking helper function to run in a thread.
    Runs a single query with pagination.
    """
    results = []
    print(f"-> Executing: {query_text}")
    
    try:
        # Initial Search
        places_result = gmaps.places(query=query_text)
        
        while True:
            if 'results' in places_result:
                for place in places_result['results']:
                    try:
                        place_id = place.get('place_id')
                        
                        # Fetch details (1 API Call)
                        # In deep scan parallel mode, we must be careful with cost.
                        # But for accuracy, we still need details.
                        details = gmaps.place(place_id=place_id, fields=['name', 'formatted_address', 'formatted_phone_number', 'website'])
                        res = details.get('result', {})
                        
                        website = res.get('website')
                        phone = res.get('formatted_phone_number')
                        
                        item = {
                            "name": res.get('name'),
                            "address": res.get('formatted_address'),
                            "phone": phone,
                            "website": website,
                            "has_website": bool(website),
                            "place_id": place_id
                        }
                        results.append(item)
                        
                        # --- Auto-Save to CSV (Thread Safe Append) ---
                        # In threads, file writing can be racey, but for a backup csv it's usually fine 
                        # or we catch the lock error.
                        try:
                            with open("leads_backup.csv", "a", newline="", encoding="utf-8") as f:
                                writer = csv.writer(f)
                                writer.writerow([
                                    item['name'],
                                    item['address'],
                                    item['phone'],
                                    item['website'],
                                    "Yes" if item['has_website'] else "No",
                                    item['place_id']
                                ])
                        except:
                            pass # Ignore CSV write collisions in parallel mode
                        # -------------------------
                        
                    except Exception as e:
                        # print(f"Error fetching details: {e}")
                        continue
            
            # Pagination Logic
            # Only fetch next page if we haven't hit the limit
            if 'next_page_token' in places_result and len(results) < max_per_query:
                token = places_result['next_page_token']
                time.sleep(2) # Mandatory 2s wait for token to become valid
                try:
                    places_result = gmaps.places(query=None, page_token=token)
                except:
                    break
            else:
                break
                
    except Exception as e:
        print(f"Error in _execute_query for '{query_text}': {e}")
        
    return results
