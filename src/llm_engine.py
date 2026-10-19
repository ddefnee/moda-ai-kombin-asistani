import os
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional
import json

load_dotenv()

class LLMEngine:
    def __init__(self, model: str = "llama-3.3-70b-versatile", provider: str = "groq"):
        """
        LLM Engine - Groq API (Llama modelleri)
        
        Args:
            model: Model adı
            provider: "groq" (Llama modelleri için)
        """
        self.model = model
        self.provider = provider.lower()
        
        if self.provider == "groq":
            try:
                from groq import Groq
                api_key = os.getenv("GROQ_API_KEY", "").strip()
                if not api_key or api_key == "your_groq_api_key_here":
                    raise ValueError(
                        "GROQ_API_KEY environment variable not set or invalid. "
                        "Please:\n"
                        "1. Go to https://console.groq.com/keys\n"
                        "2. Create an API key\n"
                        "3. Add it to your .env file: GROQ_API_KEY=your_actual_key_here\n"
                        "4. Make sure there are no spaces around the = sign"
                    )
                self.client = Groq(api_key=api_key)
                print(f"✓ Groq API bağlantısı başarılı - Model: {model}")
            except ImportError:
                raise ImportError("groq package not installed. Run: pip install groq")
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'groq'")
    
    def get_recommendation(self, prompt: str) -> Dict:
        """LLM'den kombin önerisi al - Tamamen LLM tabanlı, kural tabanlı değil"""
        system_prompt = """Sen bir moda kombinasyonu uzmanısın. Kullanıcının isteğini oku ve uygun kombinasyon öner.

ÖNEMLİ KURALLAR:

1. KULLANICI İSTEĞİNİ ANLA VE UYGUN ÜRÜNLER ÖNER:
   - Kullanıcı isteğine en yakın ürünleri seç
   - Mümkün olduğunca kullanıcı isteğine uygun ürünler öner
   - Eğer tam uygun ürün yoksa, en yakın alternatifleri öner

2. KULLANICI İSTEĞİNİ YERİNE GETİR:
   - Kullanıcının belirttiği renk, kategori, stil gibi özellikleri dikkate al
   - En uygun kombinasyonu oluştur

3. MUTLAKA ÜRÜN ÖNER:
   - Ürün listesinden mutlaka ürün seç
   - "error" veya "ürün bulunamadı" mesajı VERME
   - Her zaman kombinasyon listesi döndür

4. ÜRÜN SEÇİMİ:
   - Verilen ürün listesinden kullanıcının isteğine uygun ürünleri seç
   - Ürünlerin özniteliklerini (renk, kategori, stil, fiyat, vs.) dikkate al

5. 🚨 VERİ SETİNDEKİ GERÇEK BİLGİLERİ KULLAN (ÇOK ÖNEMLİ!):
   - Ürün listesindeki TÜM bilgileri (renk, kategori, fiyat, link, vb.) VERİ SETİNDEN OLDUĞU GİBİ kopyala
   - RENK bilgisini KESINLIKLE ürün listesindeki 'renk' alanından al, kendin tahmin etme veya değiştirme
   - Ürün listesinde belirtilen renk bilgisini kullan, görselden veya başka bir kaynaktan tahmin etme
   - Ürün bilgilerini değiştirme, sadece veri setindeki gerçek değerleri kullan

Yanıtını MUTLAKA JSON formatında ver ve MUTLAKA "kombinasyon" listesi içer."""
        
        try:
            # Groq API ile çağrı
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{prompt}\n\nLütfen yanıtınızı JSON formatında verin."}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except json.JSONDecodeError as e:
            raw_content = None
            if 'response' in locals():
                raw_content = response.choices[0].message.content
            # JSON parse hatası durumunda, içinde JSON aramaya çalış
            if raw_content:
                try:
                    import re
                    json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        return result
                except:
                    pass
            return {"error": f"JSON parse hatası: {str(e)}", "raw_response": raw_content}
        except Exception as e:
            error_msg = str(e)
            return {"error": f"Groq API hatası: {error_msg[:500]}"}



