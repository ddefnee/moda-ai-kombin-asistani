"""
LLM Girdi Üretici Modülü
Çıktıya göre LLM için uygun girdi (prompt) üretir.
"""
import json
from typing import Dict, List, Any, Optional
from .smart_query_parser import SmartQueryParser

class LLMInputGenerator:
    """Çıktı gereksinimlerine göre LLM girdisi üreten sınıf"""
    
    def __init__(self, tokenized_attributes: Dict[str, Any], 
                 semantic_meanings: Dict[str, Any],
                 learned_patterns: Dict[str, Any],
                 categories: Dict[str, List[str]],
                 smart_parser: Optional[SmartQueryParser] = None):
        """
        Args:
            tokenized_attributes: Tokenize edilmiş öznitelikler
            semantic_meanings: Semantik anlamlar
            learned_patterns: Öğrenilmiş pattern'ler
            categories: Kategorilere ayrılmış öznitelikler
            smart_parser: SmartQueryParser instance (opsiyonel)
        """
        self.tokenized_attributes = tokenized_attributes
        self.semantic_meanings = semantic_meanings
        self.learned_patterns = learned_patterns
        self.categories = categories
        self.smart_parser = smart_parser
    
    def generate_input_for_output(self, 
                                  user_query: str,
                                  products: List[Dict],
                                  reviews: Optional[List[Dict]] = None,
                                  output_requirements: Optional[Dict[str, Any]] = None) -> str:
        """
        Çıktı gereksinimlerine göre LLM girdisi üret
        
        Args:
            user_query: Kullanıcı sorgusu
            products: Ürün listesi
            reviews: Yorum listesi (opsiyonel)
            output_requirements: İstenen çıktı gereksinimleri
        
        Returns:
            LLM için hazırlanmış prompt
        """
        # Çıktı gereksinimlerini analiz et
        if output_requirements is None:
            output_requirements = self._infer_output_requirements(user_query)
        
        # Öznitelik bilgilerini çıktıya göre filtrele
        relevant_attributes = self._select_relevant_attributes(output_requirements)
        
        # Ürünleri öznitelik bilgileriyle zenginleştir
        enriched_products = self._enrich_products_with_attributes(products, relevant_attributes)
        
        # Prompt oluştur
        prompt = self._build_comprehensive_prompt(
            user_query=user_query,
            enriched_products=enriched_products,
            reviews=reviews,
            output_requirements=output_requirements,
            relevant_attributes=relevant_attributes
        )
        
        return prompt
    
    def _infer_output_requirements(self, user_query: str) -> Dict[str, Any]:
        """Kullanıcı sorgusundan çıktı gereksinimlerini çıkar - VERİ BİLİMİ TABANLI (SmartQueryParser kullanarak)"""
        query_lower = user_query.lower()
        query_original = user_query  # Orijinal sorguyu sakla
        
        requirements = {
            'output_type': 'combination',  # combination, single_product, comparison, etc.
            'required_attributes': [],
            'filters': {},
            'style_preferences': [],
            'context': 'general',
            'parsed_intent': {},  # Kullanıcının niyetini detaylı analiz
            'key_phrases': [],  # Önemli ifadeler
            'explicit_requirements': []  # Açıkça belirtilen gereksinimler
        }
        
        # SmartQueryParser kullanarak sorguyu analiz et
        if self.smart_parser:
            parsed_filters = self.smart_parser.parse_query(user_query)
            
            # Renk filtresi
            if parsed_filters.get("renk"):
                requirements['filters']['color'] = parsed_filters["renk"]
                requirements['explicit_requirements'].append(f"Renk: {parsed_filters['renk']}")
                if 'color' not in requirements['required_attributes']:
                    requirements['required_attributes'].append('color')
            
            # Kategori filtresi
            if parsed_filters.get("kategori"):
                requirements['filters']['category'] = parsed_filters["kategori"]
                requirements['explicit_requirements'].append(f"Kategori: {parsed_filters['kategori']}")
                requirements['strict_category_match'] = True
                if 'category' not in requirements['required_attributes']:
                    requirements['required_attributes'].append('category')
            
            # Stil tercihleri
            if parsed_filters.get("style_preferences"):
                requirements['style_preferences'] = parsed_filters["style_preferences"]
                for style in parsed_filters["style_preferences"]:
                    requirements['explicit_requirements'].append(f"Stil: {style}")
            
            # Bağlam
            if parsed_filters.get("context"):
                requirements['context'] = parsed_filters["context"]
                requirements['explicit_requirements'].append(f"Bağlam: {parsed_filters['context']}")
                
                # Mevsimsel faktörler
                if parsed_filters["context"] == 'winter':
                    requirements['parsed_intent']['season'] = 'winter'
                    requirements['parsed_intent']['temperature'] = 'warm'
                    requirements['explicit_requirements'].append("Mevsim: Kış - Sıcak tutan ürünler")
                elif parsed_filters["context"] == 'summer':
                    requirements['parsed_intent']['season'] = 'summer'
                    requirements['parsed_intent']['temperature'] = 'cool'
                    requirements['explicit_requirements'].append("Mevsim: Yaz - Hafif ve serin ürünler")
        
        # Çıktı tipini belirle (basit analiz)
        if any(word in query_lower for word in ['kombin', 'kombine', 'set', 'takım', 'kombinasyon']):
            requirements['output_type'] = 'combination'
        elif any(word in query_lower for word in ['karşılaştır', 'fark', 'hangi', 'hangisi']):
            requirements['output_type'] = 'comparison'
        elif any(word in query_lower for word in ['öner', 'öneri', 'iste', 'istiyorum']):
            requirements['output_type'] = 'combination'
        else:
            requirements['output_type'] = 'combination'  # Varsayılan
        
        # Gerekli öznitelikleri belirle (basit keyword matching - sadece öznitelik adları için)
        attribute_keywords = {
            'price': ['fiyat', 'price', 'ucuz', 'pahalı', 'fiyatlı', 'fiyatı'],
            'size': ['beden', 'size', 'ölçü', 'numara'],
            'brand': ['marka', 'brand', 'markası'],
            'material': ['malzeme', 'material', 'kumaş', 'fabric']
        }
        
        for attr, keywords in attribute_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                if attr not in requirements['required_attributes']:
                    requirements['required_attributes'].append(attr)
        
        # Önemli ifadeleri çıkar
        important_phrases = []
        if 'ile' in query_lower or 've' in query_lower:
            important_phrases.append("Kombinasyon isteği")
        if any(word in query_lower for word in ['öner', 'iste', 'istiyorum', 'lütfen']):
            important_phrases.append("Açık öneri isteği")
        if any(word in query_lower for word in ['uygun', 'uyumlu', 'yakışır']):
            important_phrases.append("Uyum önemli")
        
        requirements['key_phrases'] = important_phrases
        
        # Kullanıcının niyetini özetle
        intent_summary = []
        if requirements['filters']:
            intent_summary.append(f"Filtreler: {', '.join([f'{k}={v}' for k, v in requirements['filters'].items()])}")
        if requirements['style_preferences']:
            intent_summary.append(f"Stil: {', '.join(requirements['style_preferences'])}")
        if requirements['context'] != 'general':
            intent_summary.append(f"Bağlam: {requirements['context']}")
        
        requirements['parsed_intent']['summary'] = ' | '.join(intent_summary) if intent_summary else "Genel kombin isteği"
        requirements['parsed_intent']['original_query'] = query_original
        
        return requirements
    
    def _select_relevant_attributes(self, output_requirements: Dict[str, Any]) -> List[str]:
        """Çıktı gereksinimlerine göre ilgili öznitelikleri seç"""
        relevant = set()
        
        # Gerekli öznitelikler
        required = output_requirements.get('required_attributes', [])
        for req in required:
            # Öznitelik adlarında ara
            for attr_name in self.tokenized_attributes.keys():
                attr_lower = attr_name.lower()
                if req.lower() in attr_lower:
                    relevant.add(attr_name)
        
        # Filtreler için öznitelikler
        filters = output_requirements.get('filters', {})
        for filter_key in filters.keys():
            for attr_name in self.tokenized_attributes.keys():
                attr_lower = attr_name.lower()
                if filter_key.lower() in attr_lower:
                    relevant.add(attr_name)
        
        # Yüksek önemli öznitelikler (her zaman dahil)
        for attr_name, semantic in self.semantic_meanings.items():
            if semantic.get('importance_level') == 'high':
                relevant.add(attr_name)
        
        # Temel öznitelikler (her zaman dahil)
        essential_keywords = ['ad', 'name', 'fiyat', 'price', 'link', 'görsel', 'image', 'tanım', 'description']
        for attr_name in self.tokenized_attributes.keys():
            attr_lower = attr_name.lower()
            if any(keyword in attr_lower for keyword in essential_keywords):
                relevant.add(attr_name)
        
        return list(relevant)
    
    def _enrich_products_with_attributes(self, 
                                        products: List[Dict], 
                                        relevant_attributes: List[str]) -> List[Dict]:
        """Ürünleri öznitelik bilgileriyle zenginleştir"""
        enriched = []
        
        for product in products:
            enriched_product = {}
            
            # İlgili öznitelikleri ekle
            for attr in relevant_attributes:
                if attr in product:
                    value = product[attr]
                    
                    # Öznitelik bilgilerini ekle
                    token_data = self.tokenized_attributes.get(attr, {})
                    semantic = self.semantic_meanings.get(attr, {})
                    
                    enriched_product[attr] = {
                        'value': value,
                        'type': token_data.get('type'),
                        'purpose': semantic.get('likely_purpose'),
                        'importance': semantic.get('importance_level')
                    }
                else:
                    # Öznitelik yoksa, öğrenilmiş pattern'den varsayılan değer çıkar
                    enriched_product[attr] = {
                        'value': None,
                        'type': self.tokenized_attributes.get(attr, {}).get('type'),
                        'purpose': self.semantic_meanings.get(attr, {}).get('likely_purpose'),
                        'missing': True
                    }
            
            # Orijinal ürün bilgilerini de ekle
            enriched_product['_original'] = product
            enriched.append(enriched_product)
        
        return enriched
    
    def _build_comprehensive_prompt(self,
                                   user_query: str,
                                   enriched_products: List[Dict],
                                   reviews: Optional[List[Dict]],
                                   output_requirements: Dict[str, Any],
                                   relevant_attributes: List[str]) -> str:
        """Kapsamlı prompt oluştur"""
        
        # Öznitelik açıklamaları
        attribute_descriptions = self._get_attribute_descriptions(relevant_attributes)
        
        # Ürünleri sadeleştir (token tasarrufu)
        simplified_products = self._simplify_products(enriched_products, relevant_attributes)
        
        # Kullanıcı isteğini detaylı analiz et
        parsed_intent = output_requirements.get('parsed_intent', {})
        explicit_reqs = output_requirements.get('explicit_requirements', [])
        key_phrases = output_requirements.get('key_phrases', [])
        
        # Kullanıcı isteği analizi bölümü
        user_analysis_section = f"""
🎯 KULLANICI İSTEĞİ (ORİJİNAL): "{user_query}"

📋 DETAYLI ANALİZ:
"""
        
        if parsed_intent.get('summary'):
            user_analysis_section += f"- Özet: {parsed_intent['summary']}\n"
        
        if explicit_reqs:
            user_analysis_section += f"- Açıkça Belirtilen Gereksinimler:\n"
            for req in explicit_reqs:
                user_analysis_section += f"  • {req}\n"
        
        if key_phrases:
            user_analysis_section += f"- Önemli İfadeler: {', '.join(key_phrases)}\n"
        
        if output_requirements.get('filters'):
            user_analysis_section += f"- Filtreler: {json.dumps(output_requirements.get('filters', {}), ensure_ascii=False)}\n"
        
        if output_requirements.get('style_preferences'):
            user_analysis_section += f"- Stil Tercihleri: {', '.join(output_requirements.get('style_preferences', []))}\n"
        
        if output_requirements.get('context') != 'general':
            user_analysis_section += f"- Bağlam: {output_requirements.get('context', 'general')}\n"
        
        if parsed_intent.get('season'):
            user_analysis_section += f"- Mevsim: {parsed_intent.get('season')} - {parsed_intent.get('temperature', 'normal')} tutan ürünler\n"
        
        user_analysis_section += "\n"
        
        prompt = f"""Sen bir moda kombinasyonu uzmanısın. Aşağıdaki bilgileri kullanarak kullanıcının isteğini TAM OLARAK yerine getir.

{user_analysis_section}

ÇIKTI GEREKSİNİMLERİ:
- Çıktı Tipi: {output_requirements.get('output_type', 'combination')}
- Gerekli Öznitelikler: {', '.join(output_requirements.get('required_attributes', []))}

ÖZNİTELİK AÇIKLAMALARI:
{attribute_descriptions}

MEVCUT ÜRÜNLER ({len(simplified_products)} ürün):
{json.dumps(simplified_products, ensure_ascii=False, indent=2, default=str)}
"""
        
        # Yorumları ekle
        if reviews and len(reviews) > 0:
            simplified_reviews = self._simplify_reviews(reviews)
            prompt += f"""

YORUMLAR ({len(simplified_reviews)} yorum):
{json.dumps(simplified_reviews, ensure_ascii=False, indent=2, default=str)}
"""
        
        # Görev talimatları
        prompt += self._get_task_instructions(output_requirements, user_query)
        
        return prompt
    
    def _get_attribute_descriptions(self, attributes: List[str]) -> str:
        """Öznitelik açıklamalarını getir"""
        descriptions = []
        
        for attr in attributes:
            token_data = self.tokenized_attributes.get(attr, {})
            semantic = self.semantic_meanings.get(attr, {})
            
            desc = f"- {attr}: "
            desc += f"Tip={token_data.get('type', 'unknown')}, "
            desc += f"Amaç={semantic.get('likely_purpose', 'unknown')}, "
            desc += f"Önem={semantic.get('importance_level', 'unknown')}"
            
            descriptions.append(desc)
        
        return "\n".join(descriptions)
    
    def _simplify_products(self, enriched_products: List[Dict], relevant_attributes: List[str]) -> List[Dict]:
        """Ürünleri sadeleştir (token tasarrufu)"""
        simplified = []
        
        for enriched in enriched_products[:8]:  # Maksimum 8 ürün (token tasarrufu)
            original = enriched.get('_original', {})
            simple_product = {}
            
            # Temel bilgiler
            for attr in relevant_attributes[:5]:  # Maksimum 5 öznitelik (token tasarrufu)
                if attr in enriched:
                    attr_data = enriched[attr]
                    value = attr_data.get('value')
                    
                    if value is not None:
                        # Değeri string'e çevir ve kısalt
                        str_value = str(value)
                        if len(str_value) > 100:
                            str_value = str_value[:100] + "..."
                        simple_product[attr] = str_value
            
            # Orijinal üründen kritik alanları ekle
            # urun_linki-href öncelikli olarak kullan
            if 'urun_linki-href' in original and 'urun_linki-href' not in simple_product:
                simple_product['urun_linki-href'] = original['urun_linki-href']
            elif 'urun_linki' in original and 'urun_linki' not in simple_product:
                simple_product['urun_linki'] = original['urun_linki']
            
            # Kritik alanları ekle - özellikle renk bilgisi
            for key in ['urun_tanimi', 'urun_fiyat', 'urun_gorsel', 'renk', 'color', 'urun_rengi']:
                if key in original and key not in simple_product:
                    simple_product[key] = original[key]
            
            simplified.append(simple_product)
        
        return simplified
    
    def _simplify_reviews(self, reviews: List[Dict]) -> List[Dict]:
        """Yorumları sadeleştir"""
        simplified = []
        
        for review in reviews[:2]:  # Maksimum 2 yorum (token tasarrufu)
            simple_review = {}
            
            # Kritik alanlar
            for key in ['yorum', 'yildiz', 'rating', 'comment']:
                if key in review:
                    value = str(review[key])
                    if len(value) > 100:  # Daha kısa yorumlar (token tasarrufu)
                        value = value[:100] + "..."
                    simple_review[key] = value
            
            if simple_review:
                simplified.append(simple_review)
        
        return simplified
    
    def _get_task_instructions(self, output_requirements: Dict[str, Any], user_query: str) -> str:
        """Görev talimatlarını getir"""
        output_type = output_requirements.get('output_type', 'combination')
        
        # Kullanıcı isteğinden kritik bilgileri çıkar
        query_lower = user_query.lower()
        required_category = output_requirements.get('filters', {}).get('category', '')
        required_color = output_requirements.get('filters', {}).get('color', '')
        strict_category = output_requirements.get('strict_category_match', False)
        
        # Kullanıcı isteğini vurgula - çok güçlü vurgular
        user_requirement_section = f"""
🚨🚨🚨 KULLANICI İSTEĞİ - MUTLAKA OKU VE UYGULA 🚨🚨🚨
ORİJİNAL İSTEK: "{user_query}"

"""
        
        # Açıkça belirtilen gereksinimleri vurgula
        explicit_reqs = output_requirements.get('explicit_requirements', [])
        if explicit_reqs:
            user_requirement_section += "AÇIKÇA BELİRTİLEN GEREKSİNİMLER:\n"
            for req in explicit_reqs:
                user_requirement_section += f"  ⚠️ {req}\n"
            user_requirement_section += "\n"
        
        if required_category and strict_category:
            user_requirement_section += f"""
🚨 KRİTİK KULLANICI İSTEĞİ 🚨
KULLANICI "{required_category.upper()}" KATEGORİSİNDE ÜRÜN İSTİYOR!
- SADECE {required_category} kategorisinden ürün öner
- {required_category} dışında HİÇBİR kategori önerme (pantolon, etek, ceket, vs. ÖNERME)
- Eğer ürün listesinde {required_category} yoksa, başka kategori önerme - "uygun_urun_bulunamadi" mesajı ver

"""
        if required_color:
            user_requirement_section += f"""
🚨 KRİTİK KULLANICI İSTEĞİ 🚨
KULLANICI "{required_color.upper()}" RENKTE ÜRÜN İSTİYOR!
- SADECE {required_color} renkli ürünler öner
- {required_color} dışında HİÇBİR renk önerme
- Eğer ürün listesinde {required_color} renkli ürün yoksa, başka renk önerme - "uygun_urun_bulunamadi" mesajı ver

"""
        
        if output_type == 'combination':
            return f"""
🧠 AKILLI KOMBİNASYON OLUŞTURMA YAKLAŞIMI:

1. KULLANICI İSTEĞİNİ DERİNLEMESİNE ANLA (EN ÖNEMLİ ADIM!):
   - Yukarıdaki "KULLANICI İSTEĞİ" bölümünü MUTLAKA oku ve anla
   - İsteği kelime kelime analiz et, her detayı yakala
   - Gizli bağlamları ve anlamları anla (örn: "toplantı" = profesyonel stil)
   - Kullanıcının gerçek ihtiyacını ve amacını kavra
   - Mevsimsel, hava durumu, etkinlik tipi gibi faktörleri değerlendir
   - Kullanıcının belirttiği tüm gereksinimleri (renk, kategori, stil, vb.) MUTLAKA karşıla
   - Eğer kullanıcı spesifik bir şey istiyorsa (örn: "kırmızı elbise"), SADECE o şeyi öner

2. ÜRÜNLERİ AKILLICA DEĞERLENDİR:
   - Her ürünü kullanıcı isteğine göre zihinsel olarak puanla
   - Sadece yüzey özelliklere değil, ürünün karakterine ve uyumuna bak
   - Ürünlerin birbirleriyle nasıl uyum sağlayacağını düşün
   - Renk uyumu, stil uyumu, kategori uyumu, fiyat uyumu gibi tüm faktörleri değerlendir

3. KOMBİNASYON MANTIĞI:
   - Ana parçayı belirle (kullanıcının isteğine en uygun olan)
   - Ana parçaya uyumlu ikincil parçaları seç (çanta, ayakkabı, aksesuar)
   - Renk paletini dengeli tut (monokrom veya uyumlu renk kombinasyonları)
   - Stil tutarlılığını koru (tüm parçalar aynı stil dilinde)
   - Fiyat dengesini göz önünde bulundur

4. BAĞLAMSAL DÜŞÜNME:
   - "Toplantı/iş" → Profesyonel, şık, dikkat çekici değil, güvenilir
   - "Günlük" → Rahat, pratik, konforlu, fonksiyonel
   - "Kış/kar" → Sıcak tutan, koruyucu, katmanlı, dayanıklı
   - "Yaz" → Hafif, nefes alan, serin, rahat
   - "Akşam/parti" → Şık, özel, dikkat çekici, zarif
   - "Rahat" → Konforlu, esnek, pratik
   - "Şık" → Zarif, sofistike, dikkat çekici

5. ÜRÜN SEÇİMİNDE AKILLILIK:
   - Mükemmel uyum varsa onu seç
   - Mükemmel yoksa, en iyi alternatifi bul ve nedenini açıkla
   - Kullanıcı isteğine TAM UYGUN olmayan ürünleri önerme
   - Ama esnek ol - bazen yakın alternatifler de mükemmel kombinasyonlar oluşturabilir
   - Her seçiminin nedenini detaylı açıkla

6. KOMBİNASYON TAMAMLIĞI:
   - Minimum 3-4 parça: ana parça + çanta + ayakkabı + (gerekirse aksesuar)
   - Her parça bir amaca hizmet etmeli
   - Gereksiz parça ekleme, eksik parça bırakma
   - Tüm parçalar birbiriyle uyumlu ve tutarlı olmalı

ÇIKTI FORMATI (JSON):
{{
    "kombinasyon": [
        {{
            "urun_tanimi": "Ürün adı (ürün listesindeki 'ad' veya 'urun_tanimi' alanından KESINLIKLE kopyala)",
            "urun_linki": "Link (ürün listesindeki 'link' veya 'urun_linki' alanından KESINLIKLE kopyala)",
            "urun_fiyat": "Fiyat (ürün listesindeki 'fiyat' veya 'urun_fiyat' alanından KESINLIKLE kopyala)",
            "urun_gorsel": "Görsel linki (ürün listesindeki 'gorsel' veya 'urun_gorsel' alanından KESINLIKLE kopyala)",
            "secme_nedeni": "Neden seçildi - kullanıcı isteğine nasıl uyduğunu açıkla",
            "onemli_ozellikler": {{
                "renk": "ÜRÜN LİSTESİNDEKİ 'renk' ALANINDAN KESINLIKLE KOPYALA - VERİ SETİNDEKİ GERÇEK RENK BİLGİSİNİ KULLAN, KENDİN TAHMİN ETME!",
                "kategori": "Ürün listesindeki 'kat' veya 'kategori' alanından kopyala",
                "stil": "Ürün listesindeki 'stil' alanından kopyala (varsa)"
            }}
        }}
    ],
    "aciklama": "Kombinasyon açıklaması - kullanıcı isteğine nasıl uyduğunu belirt",
    "stil_notlari": "Stil önerileri",
    "uyum_analizi": "Uyum analizi"
}}

🚨 KRİTİK KURAL: 
- Ürün listesindeki TÜM bilgileri (renk, kategori, fiyat, link, vb.) VERİ SETİNDEN OLDUĞU GİBİ kopyala
- RENK bilgisini KESINLIKLE veri setindeki 'renk' alanından al, kendin tahmin etme veya değiştirme
- Ürün listesinde belirtilen renk bilgisini kullan, görselden veya başka bir kaynaktan tahmin etme
"""
        else:
            return f"""
{user_requirement_section}

GÖREV - KULLANICI İSTEĞİNİ YERİNE GETİR:

KRİTİK KURALLAR:
1. KULLANICI İSTEĞİNE UYGUN OLMAYAN ÜRÜNLERİ ASLA ÖNERME
2. Kullanıcının belirttiği tüm kriterleri MUTLAKA karşıla
3. Ürün listesinden kullanıcının isteğine TAM UYGUN ürünleri seç
4. Öznitelik bilgilerini kullanarak akıllıca seçim yap

ÇIKTI FORMATI (JSON):
{{
    "sonuc": [...],
    "aciklama": "..."
}}
"""


