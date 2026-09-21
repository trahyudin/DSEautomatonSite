import os
import google.generativeai as genai
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image

# Muat variabel lingkungan
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("[WARNING] GEMINI_API_KEY not found in .env. Vision features will fail.")

def ask_gemini_text(prompt, model_name="gemini-3.6-flash", require_json=True):
    if not GEMINI_API_KEY:
        return "", "No GEMINI_API_KEY found"
    import time
    import random
    last_error = ""
    for attempt in range(4): # Increase to 4 attempts
        try:
            model = genai.GenerativeModel(model_name)
            
            # Configure JSON if required
            gen_config = None
            if require_json:
                gen_config = genai.types.GenerationConfig(response_mime_type="application/json")
                
            response = model.generate_content(prompt, generation_config=gen_config)
            if response and response.text:
                return response.text.strip(), ""
        except Exception as e:
            last_error = str(e)
            if attempt < 3:
                wait_time = (2 ** attempt) * 3 + random.uniform(0.5, 1.5)
                print(f"Gemini Text API Error/Rate Limit. Retrying in {wait_time:.1f}s... ({last_error})")
                time.sleep(wait_time)
            else:
                print(f"Gemini Text API Error after 4 attempts: {last_error}")
    return "", last_error

def inject_som_markers(page):
    """
    Menyuntikkan Set-of-Mark (SoM) ke halaman web.
    Menggambar kotak merah berserta nomor unik di atas setiap elemen interaktif.
    """
    js_code = """
    () => {
        // Hapus marker lama jika ada
        document.querySelectorAll('.som-marker-box').forEach(el => el.remove());
        
        let counter = 1;
        const elements = document.querySelectorAll('button, a, input, textarea, [role="button"], [contenteditable="true"]');
        const som_mapping = {};
        
        elements.forEach(el => {
            const rect = el.getBoundingClientRect();
            // Hanya tandai elemen yang terlihat di layar
            if (rect.width > 0 && rect.height > 0 && rect.top >= 0 && rect.top <= window.innerHeight) {
                const id = counter++;
                som_mapping[id] = el;
                
                // Buat kotak merah
                const box = document.createElement('div');
                box.className = 'som-marker-box';
                box.style.position = 'absolute';
                box.style.left = (rect.left + window.scrollX) + 'px';
                box.style.top = (rect.top + window.scrollY) + 'px';
                box.style.width = rect.width + 'px';
                box.style.height = rect.height + 'px';
                box.style.border = '2px solid red';
                box.style.pointerEvents = 'none';
                box.style.zIndex = 2147483647; // Max z-index
                
                // Buat label nomor
                const label = document.createElement('div');
                label.innerText = id;
                label.style.position = 'absolute';
                label.style.background = 'red';
                label.style.color = 'white';
                label.style.fontSize = '12px';
                label.style.fontWeight = 'bold';
                label.style.padding = '2px 4px';
                label.style.top = '-15px';
                label.style.left = '-2px';
                
                box.appendChild(label);
                document.body.appendChild(box);
                
                // Simpan atribut unik untuk referensi dari Python
                el.setAttribute('data-som-id', id);
            }
        });
        return counter - 1; // Kembalikan jumlah elemen yang ditandai
    }
    """
    count = page.evaluate(js_code)
    return count

def remove_som_markers(page):
    page.evaluate("() => document.querySelectorAll('.som-marker-box').forEach(el => el.remove())")

def ask_gemini_vision(screenshot_bytes, prompt, model_name="gemini-1.5-flash"):
    """
    Mengirimkan screenshot (berisi SOM) dan prompt ke Gemini.
    Mengembalikan jawaban JSON terstruktur (e.g. {"action": "click", "id": 42}).
    """
    if not GEMINI_API_KEY:
        return None
        
    import json
    import time
        
    try:
        # Load image from bytes
        img = Image.open(BytesIO(screenshot_bytes))
        
        # Configure model (using gemini-3.6-flash by default for best visual reasoning)
        model = genai.GenerativeModel(model_name)
        
        # Create full prompt ensuring AI replies strictly with JSON
        full_prompt = (
            "You are an expert web automation agent operating a browser.\n"
            "The attached screenshot contains interactive elements highlighted with red bounding boxes and unique ID numbers.\n"
            f"{prompt}\n\n"
            "Reply STRICTLY with a valid JSON object matching the requested format. Do not include markdown code blocks (like ```json), just the raw JSON."
        )
        
        for attempt in range(3):
            try:
                response = model.generate_content([full_prompt, img])
                text = response.text.strip()
                # Clean markdown if AI ignores instruction
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                
                return json.loads(text.strip())
            except Exception as e:
                if attempt < 2:
                    print(f"Gemini Vision API Error/Rate Limit. Retrying in 10s... ({str(e)})")
                    time.sleep(10)
                else:
                    print(f"Gemini Vision API Error after 3 attempts: {e}")
                    return None
                    
        return None
        
    except Exception as e:
        print(f"Gemini Vision Pre-processing Error: {e}")
        return None
