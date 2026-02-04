import os
import json
import httpx
import random

async def generate_landing_page(business_name: str, niche: str, location: str, api_key: str, provider: str = "openai") -> str:
    """
    Generates a single-page HTML landing page using an AI Provider (OpenAI or Gemini).
    """
    
    prompt = f"""
    You are an expert web developer. capture the essence of this business:
    Business Name: {business_name}
    Niche: {niche}
    Location: {location}
    
    Task: Create a stunning, high-converting, single-page landing page for this business.
    
    Requirements:
    1. Use Tailwind CSS via CDN for all styling.
    2. The design MUST be modern, clean, and professional (Dark mode or Light mode, whichever fits the niche best).
    3. Include sections: Hero (with catchy headline), Services, About Us, Testimonials (make up 2 realistic ones), and Contact Form (visual only).
    4. Use "https://source.unsplash.com/1600x900/?{niche}" for the hero background image.
    5. Use "https://source.unsplash.com/800x600/?{niche},work" for service images.
    6. Return ONLY the raw HTML code. Do not wrap in markdown code blocks. Start with <!DOCTYPE html>.
    """
    
    # Wrap API calls in try/except to fallback
    try:
        # 1. OpenAI Implementation
        if provider == "openai" or provider == "gpt":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            data = {
                "model": "gpt-4o", # Or gpt-3.5-turbo if 4o fails/too expensive
                "messages": [
                    {"role": "system", "content": "You are a world-class frontend developer."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, headers=headers, json=data)
                resp.raise_for_status()
                result = resp.json()
                content = result['choices'][0]['message']['content']
                return _clean_html(content)

        # 2. Gemini Implementation (Alternative)
        elif provider == "gemini":
            # Try 1.5-flash first (cheaper/faster), then pro
            models = ["gemini-1.5-flash", "gemini-pro"]
            last_error = None
            
            for model in models:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                    headers = {"Content-Type": "application/json"}
                    data = {"contents": [{"parts": [{"text": prompt}]}]}
                    
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        resp = await client.post(url, headers=headers, json=data)
                        resp.raise_for_status()
                        result = resp.json()
                        content = result['candidates'][0]['content']['parts'][0]['text']
                        return _clean_html(content)
                except Exception as e:
                    last_error = e
                    continue
            
            # If both failed, raise the last error
            if last_error:
                raise last_error
                
        else:
            raise ValueError("Unsupported provider")

    except Exception as e:
        print(f"AI Generation failed ({e}). Using Fallback Template.")
        return _generate_fallback_template(business_name, niche, location)

def _clean_html(content):
    """Removes markdown code blocks."""
    return content.replace("```html", "").replace("```", "")

import urllib.parse

def _generate_fallback_template(business_name, niche, location):
    # ---------------------------------------------------------
    # 1. PROCEDURAL DESIGN ENGINE
    # ---------------------------------------------------------
    
    # Clean Inputs
    niche_display = niche.title().replace("Plumbers", "Plumbing").replace("Roofers", "Roofing")
    
    # Palettes (Primary Colors)
    palettes = [
        {"name": "Blue", "primary": "blue", "code": "#2563eb"},
        {"name": "Indigo", "primary": "indigo", "code": "#4f46e5"},
        {"name": "Emerald", "primary": "emerald", "code": "#059669"},
        {"name": "Violet", "primary": "violet", "code": "#7c3aed"},
        {"name": "Cyan", "primary": "cyan", "code": "#0891b2"},
        {"name": "Rose", "primary": "rose", "code": "#e11d48"},
    ]
    palette = random.choice(palettes)
    pri = palette["primary"]
    
    # Fonts
    fonts = [
        {"name": "Plus Jakarta Sans", "url": "Plus+Jakarta+Sans:wght@300;400;500;600;700;800"},
        {"name": "Outfit", "url": "Outfit:wght@300;400;500;600;700;800"},
        {"name": "Inter", "url": "Inter:wght@300;400;500;600;700;800"},
        {"name": "Poppins", "url": "Poppins:wght@300;400;500;600;700;800"},
    ]
    font = random.choice(fonts)
    
    # Hero Layouts
    layouts = ["split", "centered", "minimal"]
    layout = random.choice(layouts)

    # ---------------------------------------------------------
    # 2. AI IMAGE GENERATION (Robust URL)
    # ---------------------------------------------------------
    def get_ai_img(prompt, width=800, height=600):
        # Enhance prompt with business details for uniqueness
        full_prompt = f"{prompt}, related to {niche} in {location}, high quality, 4k"
        encoded_prompt = urllib.parse.quote(full_prompt)
        seed = random.randint(1, 99999)
        # Use image.pollinations.ai directly
        return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=true"

    hero_img_prompt = f"cinematic shot of modern {niche} business storefront or service in action, {location}, professional photography, 8k"
    hero_img = get_ai_img(hero_img_prompt, 1600, 900)
    
    service_imgs = [
        get_ai_img(f"professional {niche} service close up action shot, highly detailed", 800, 600) for _ in range(3)
    ]
    
    # ---------------------------------------------------------
    # 3. TEMPLATE CONSTRUCTION
    # ---------------------------------------------------------
    
    # Dynamic Hero Sections
    hero_html = ""
    if layout == "split":
        hero_html = f"""
        <div class="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                <div class="grid lg:grid-cols-2 gap-12 lg:gap-8 items-center">
                    <div class="max-w-2xl">
                        <div class="inline-flex items-center px-4 py-2 rounded-full bg-white border border-slate-200 shadow-sm mb-6">
                            <span class="flex h-2 w-2 rounded-full bg-{pri}-500 mr-2"></span>
                            <span class="text-xs font-semibold uppercase tracking-wide text-slate-600">Serving {location}</span>
                        </div>
                        <h1 class="text-5xl lg:text-7xl font-extrabold tracking-tight text-slate-900 leading-[1.1] mb-6">
                            {niche_display} <span class="text-transparent bg-clip-text bg-gradient-to-r from-{pri}-600 to-{pri}-400">Excellence.</span>
                        </h1>
                        <p class="text-lg text-slate-600 mb-8 leading-relaxed max-w-lg">
                            Premier {niche_display} services for {location}. We deliver quality, reliability, and professional results every time.
                        </p>
                        <div class="flex flex-col sm:flex-row gap-4">
                            <a href="#contact" class="inline-flex justify-center items-center px-8 py-4 text-base font-bold rounded-xl text-white bg-{pri}-600 shadow-lg shadow-{pri}-500/30 hover:bg-{pri}-700 hover:shadow-{pri}-500/50 transition-all transform hover:-translate-y-1">
                                Get a Quote
                            </a>
                        </div>
                    </div>
                    <div class="relative lg:h-[600px] w-full hidden lg:block">
                        <div class="relative z-10 rounded-3xl overflow-hidden shadow-2xl shadow-slate-900/10 border border-white/20 transform rotate-2 hover:rotate-0 transition-all duration-700">
                            <img src="{hero_img}" alt="{niche}" class="w-full h-full object-cover" onerror="this.src='https://placehold.co/800x600?text=Service+Image'">
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    elif layout == "centered":
        hero_html = f"""
        <div class="relative py-32 lg:py-48 overflow-hidden bg-slate-900">
             <div class="absolute inset-0">
                <img src="{hero_img}" class="w-full h-full object-cover opacity-30" onerror="this.src='https://placehold.co/1600x900?text=Hero+Image'">
                <div class="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent"></div>
             </div>
             <div class="relative z-10 max-w-4xl mx-auto text-center px-4">
                <h1 class="text-5xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.1] mb-6 drop-shadow-lg">
                    {business_name}
                </h1>
                <p class="text-xl text-slate-200 mb-10 max-w-2xl mx-auto drop-shadow-md">
                    Top-Rated {niche_display} Services in {location}.
                </p>
                <a href="#contact" class="inline-flex justify-center items-center px-8 py-4 text-base font-bold rounded-xl text-white bg-{pri}-600 shadow-lg shadow-{pri}-500/30 hover:bg-{pri}-700 transition-all transform hover:-translate-y-1">
                    Book Appointment
                </a>
             </div>
        </div>
        """
    else: # minimal
        hero_html = f"""
        <div class="relative pt-40 pb-20 bg-slate-50">
            <div class="max-w-7xl mx-auto px-4 text-center">
                <span class="text-{pri}-600 font-bold tracking-wider uppercase text-sm mb-4 block">Professional {niche_display}</span>
                <h1 class="text-6xl font-black text-slate-900 mb-8">{business_name}</h1>
                <div class="max-w-4xl mx-auto h-[500px] rounded-3xl overflow-hidden shadow-2xl mb-12 relative group">
                     <img src="{hero_img}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" onerror="this.src='https://placehold.co/1600x900?text=Hero'">
                     <div class="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-colors"></div>
                </div>
                <div class="flex justify-center gap-4">
                     <a href="#contact" class="px-8 py-3 bg-slate-900 text-white rounded-lg font-bold hover:bg-slate-800 transition">Contact Us</a>
                </div>
            </div>
        </div>
        """

    return f"""
<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} | {niche_display} in {location}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family={font['url']}&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    fontFamily: {{
                        sans: ['"{font['name']}"', 'sans-serif'],
                    }},
                    colors: {{
                        primary: {{
                            50: '#f0f9ff',
                            100: '#e0f2fe',
                            500: '{palette['code']}',
                            600: '{palette['code']}', // simplified for proc. gen
                            700: '#334155',
                        }}
                    }}
                }}
            }}
        }}
    </script>
</head>
<body class="font-sans antialiased text-slate-800 bg-white" x-data="{{ mobileMenu: false }}">

    <!-- Navigation -->
    <nav class="fixed w-full z-50 bg-white/90 backdrop-blur-md border-b border-slate-100 transition-all duration-300">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-20 items-center">
                <div class="flex-shrink-0 flex items-center gap-2">
                    <div class="w-10 h-10 rounded-xl bg-{pri}-600 flex items-center justify-center text-white font-bold text-xl shadow-lg">
                        {business_name[0]}
                    </div>
                    <span class="font-bold text-xl tracking-tight text-slate-900">{business_name}</span>
                </div>
                <div class="hidden md:flex items-center space-x-8">
                    <a href="#services" class="text-sm font-medium text-slate-600 hover:text-{pri}-600 transition-colors">Services</a>
                    <a href="#contact" class="px-6 py-2.5 rounded-full bg-slate-900 text-white text-sm font-semibold shadow-lg hover:bg-slate-800 transition-all">
                        Get a Quote
                    </a>
                </div>
            </div>
        </div>
    </nav>

    {hero_html}

    <!-- Services -->
    <div id="services" class="py-24 bg-slate-50 relative">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center max-w-3xl mx-auto mb-16">
                <h3 class="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">Our Services</h3>
                <p class="text-lg text-slate-600">Professional {niche_display} solutions tailored for you.</p>
            </div>
            <div class="grid md:grid-cols-3 gap-8">
                <!-- Service Cards -->
                <div class="bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 group">
                    <div class="h-48 overflow-hidden">
                        <img src="{service_imgs[0]}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" onerror="this.src='https://placehold.co/800x600?text=Service+1'">
                    </div>
                    <div class="p-6">
                        <h4 class="text-xl font-bold mb-2">Residential</h4>
                        <p class="text-slate-500">Complete home {niche_display} services.</p>
                    </div>
                </div>
                <div class="bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 group">
                    <div class="h-48 overflow-hidden">
                        <img src="{service_imgs[1]}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" onerror="this.src='https://placehold.co/800x600?text=Service+2'">
                    </div>
                    <div class="p-6">
                        <h4 class="text-xl font-bold mb-2">Commercial</h4>
                        <p class="text-slate-500">Business-grade solutions.</p>
                    </div>
                </div>
                <div class="bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 group">
                    <div class="h-48 overflow-hidden">
                        <img src="{service_imgs[2]}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" onerror="this.src='https://placehold.co/800x600?text=Service+3'">
                    </div>
                    <div class="p-6">
                        <h4 class="text-xl font-bold mb-2">Emergency</h4>
                        <p class="text-slate-500">24/7 Rapid Response.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Contact -->
    <div id="contact" class="py-24 bg-slate-900 text-white text-center">
        <h2 class="text-4xl font-bold mb-6">Need a {niche_display}?</h2>
        <p class="text-xl text-slate-300 mb-10">Contact {business_name} now.</p>
        <button class="px-8 py-4 bg-{pri}-600 rounded-xl font-bold hover:bg-{pri}-500 transition-all">Call Now</button>
    </div>

</body>
</html>
"""
