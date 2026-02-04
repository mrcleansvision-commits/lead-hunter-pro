import googlemaps
import time
import csv
import os
from typing import List, Dict, Optional

async def search_google_maps(niche: str, location: str, max_results: int = 60, api_key: str = None, deep_scan: bool = False) -> List[Dict]:
    """
    Searches Google Places API for businesses.
    Supports 'deep_scan' to bypass 60-result limit by creating sub-region queries.
    """
    if not api_key:
        raise ValueError("Google API Key is required")

    # Initialize client
    gmaps = googlemaps.Client(key=api_key)
    
    # Define queries
    queries = [f"{niche} in {location}"]
    if deep_scan:
        from services.cities import US_STATES_CITIES
        loc_lower = location.lower().strip()
        
        # Check if input is a state
        if loc_lower in US_STATES_CITIES:
            print(f"State Mode Activated for: {location.title()}")
            target_cities = US_STATES_CITIES[loc_lower]
            for city in target_cities:
                # For each city, we add it to the query list
                # We do NOT run the full 8-point grid per city to avoid hitting API rate limits instantly
                # unless specifically requested? 
                # Let's keep it simple: State Mode = 1 search per major city.
                # That's 15-20 highly targeted searches.
                queries.append(f"{niche} in {city}, {location}")
        else:
            print(f"Deep Scan Enabled: Generating 8-Point Grid queries for {location}")
            # Maximum Area Coverage Strategy (City Level)
            directions = [
                "North", "North East", "East", "South East", 
                "South", "South West", "West", "North West",
                "Central", "Downtown"
            ]
            for direction in directions:
                queries.append(f"{niche} in {direction} {location}")
            
    all_results = {} # place_id -> result_dict to deduplicate
    
    for query in queries:
        print(f"Executing Query: {query}")
        try:
            # Execute search for this query
            # We enforce a mini-max of 60 per query because that's Google's limit anyway
            # But the total across all queries can exceed 60
            query_results = _execute_query(gmaps, query, max_per_query=60)
            
            for res in query_results:
                pid = res['place_id']
                if pid not in all_results:
                    all_results[pid] = res
                    
            # Stop if we have "enough" global results (e.g. 5x max_results requested)
            # Or just let it run to get as many as possible.
            # Let's cap it at max_results * 5 to be safe/reasonable cost
            # Removed Limit: Will run until Google runs out of results for the query grid
            if False: # Disabled manual cap
                break
                
        except Exception as e:
            print(f"Query failed for '{query}': {e}")
            continue
            
    return list(all_results.values())

def _execute_query(gmaps, query_text, max_per_query=60):
    """Helper to run a single query with pagination."""
    results = []
    
    try:
        # Initial Search
        places_result = gmaps.places(query=query_text)
        
        while True:
            if 'results' in places_result:
                print(f"  - Found {len(places_result['results'])} results on this page.")
                
                for place in places_result['results']:
                    place_id = place.get('place_id')
                    
                    # Optimization: In Deep Scan, we might want to skip details fetching for duplicates
                    # But we don't know duplicates yet. 
                    # We will fetch details here. Cost is 1 request per result.
                    
                    try:
                        # Fetch details (Phone, Website)
                        # We use fields to limit cost
                        details = gmaps.place(place_id=place_id, fields=['name', 'formatted_address', 'formatted_phone_number', 'website'])
                        res = details.get('result', {})
                        
                        website = res.get('website')
                        phone = res.get('formatted_phone_number')
                        
                        results.append({
                            "name": res.get('name'),
                            "address": res.get('formatted_address'),
                            "phone": phone,
                            "website": website,
                            "has_website": bool(website),
                            "place_id": place_id
                        })
                        
                        # --- Auto-Save to CSV ---
                        try:
                            file_exists = os.path.isfile("leads_backup.csv")
                            with open("leads_backup.csv", "a", newline="", encoding="utf-8") as f:
                                writer = csv.writer(f)
                                if not file_exists:
                                    writer.writerow(["Name", "Address", "Phone", "Website", "Has Website", "Place ID"])
                                
                                writer.writerow([
                                    res.get('name'),
                                    res.get('formatted_address'),
                                    phone,
                                    website,
                                    "Yes" if website else "No",
                                    place_id
                                ])
                        except Exception as csv_err:
                            print(f"Failed to auto-save lead: {csv_err}")
                        # -------------------------
                        
                    except Exception as e:
                        print(f"Error fetching details: {e}")
                        continue
            
            # Pagination
            if 'next_page_token' in places_result and len(results) < max_per_query:
                token = places_result['next_page_token']
                print("  - Fetching next page (waiting 2s)...")
                time.sleep(2) # Mandatory wait for token validation
                try:
                    places_result = gmaps.places(query=None, page_token=token)
                except Exception as e:
                    print(f"Pagination error: {e}")
                    break
            else:
                break
                
    except Exception as e:
        print(f"Error in _execute_query: {e}")
        
    return results
