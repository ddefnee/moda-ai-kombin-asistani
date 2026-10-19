"""
Model Çıktı Seçici Modülü
LLM çıktısından uygun parçaları seçer ve filtreler.
"""
import json
import re
from typing import Dict, List, Any, Optional

class ModelSelector:
    """LLM çıktısından uygun parçaları seçen sınıf"""
    
    def __init__(self, output_requirements: Dict[str, Any],
                 learned_patterns: Dict[str, Any],
                 semantic_meanings: Dict[str, Any]):
        """
        Args:
            output_requirements: Çıktı gereksinimleri
            learned_patterns: Öğrenilmiş pattern'ler
            semantic_meanings: Semantik anlamlar
        """
        self.output_requirements = output_requirements
        self.learned_patterns = learned_patterns
        self.semantic_meanings = semantic_meanings
    
    def select_output(self, llm_response: Any) -> Dict[str, Any]:
        """
        LLM yanıtından uygun çıktıyı seç - LLM'in seçimine güven
        
        Args:
            llm_response: LLM'den gelen ham yanıt (dict veya string)
        
        Returns:
            Seçilmiş çıktı
        """
        # LLM yanıtını parse et
        parsed_response = self._parse_llm_response(llm_response)
        
        if not parsed_response:
            return {"error": "LLM yanıtı parse edilemedi"}
        
        # Eğer LLM hata mesajı döndürmüşse, onu olduğu gibi döndür
        if isinstance(parsed_response, dict) and 'error' in parsed_response:
            return parsed_response
        
        # Çıktı tipine göre seçim yap
        output_type = self.output_requirements.get('output_type', 'combination')
        
        if output_type == 'combination':
            return self._select_combination_output(parsed_response)
        elif output_type == 'comparison':
            return self._select_comparison_output(parsed_response)
        else:
            return self._select_general_output(parsed_response)
    
    def _parse_llm_response(self, response: Any) -> Optional[Dict[str, Any]]:
        """LLM yanıtını parse et"""
        if isinstance(response, dict):
            return response
        elif isinstance(response, str):
            # JSON içinde JSON arama
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # JSON bloğu bulmaya çalış
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except:
                        pass
                return None
        else:
            return None
    
    def _select_combination_output(self, parsed_response: Dict[str, Any]) -> Dict[str, Any]:
        """Kombinasyon çıktısını seç - LLM'in seçimine güven, filtreleme yapma"""
        selected = {
            'kombinasyon': [],
            'aciklama': parsed_response.get('aciklama', ''),
            'stil_notlari': parsed_response.get('stil_notlari', ''),
            'uyum_analizi': parsed_response.get('uyum_analizi', '')
        }
        
        # Kombinasyon listesini al
        kombinasyon = parsed_response.get('kombinasyon', [])
        
        if not isinstance(kombinasyon, list):
            return {"error": "Kombinasyon listesi bulunamadı"}
        
        # LLM'in döndürdüğü tüm ürünleri olduğu gibi kabul et
        # LLM zaten kullanıcı isteğine göre en uygun ürünleri seçiyor
        for item in kombinasyon:
            if not isinstance(item, dict):
                continue
            
            # Gerekli alanları kontrol et - en az bir tanesi olmalı
            if not item.get('urun_tanimi') and not item.get('urun_linki'):
                continue  # Kritik alanlar eksik
            
            # Ürünü zenginleştir ve ekle
            enriched_item = self._enrich_item(item)
            selected['kombinasyon'].append(enriched_item)
        
        # Eğer hiç ürün yoksa, LLM'in döndürdüğü yanıtı olduğu gibi döndür
        # (LLM zaten hata mesajı döndürmüş olabilir)
        if len(selected['kombinasyon']) == 0:
            # LLM'in döndürdüğü yanıtta hata varsa onu kullan
            if 'error' in parsed_response:
                return parsed_response
            # Yoksa, boş kombinasyon listesi ile döndür (hata mesajı verme)
            # Çünkü LLM zaten ürün önermiş olmalı
            pass
        
        return selected
    
    def _select_comparison_output(self, parsed_response: Dict[str, Any]) -> Dict[str, Any]:
        """Karşılaştırma çıktısını seç"""
        return {
            'karsilastirma': parsed_response.get('karsilastirma', parsed_response.get('comparison', [])),
            'sonuc': parsed_response.get('sonuc', parsed_response.get('result', '')),
            'aciklama': parsed_response.get('aciklama', '')
        }
    
    def _select_general_output(self, parsed_response: Dict[str, Any]) -> Dict[str, Any]:
        """Genel çıktıyı seç"""
        return parsed_response
    
    def _enrich_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Ürün öğesini zenginleştir"""
        enriched = item.copy()
        
        # Eksik alanları doldur
        if 'onemli_ozellikler' not in enriched:
            enriched['onemli_ozellikler'] = {}
        
        # Özniteliklerden önemli bilgileri çıkar
        for key, value in item.items():
            if key not in ['urun_tanimi', 'urun_linki', 'urun_fiyat', 'urun_gorsel', 'secme_nedeni', 'onemli_ozellikler']:
                # Önemli özellik olarak ekle
                semantic = self.semantic_meanings.get(key, {})
                purpose = semantic.get('likely_purpose', '')
                
                if purpose in ['color', 'renk']:
                    enriched['onemli_ozellikler']['renk'] = str(value)
                elif purpose in ['category', 'kategori']:
                    enriched['onemli_ozellikler']['kategori'] = str(value)
                elif purpose in ['size', 'beden']:
                    enriched['onemli_ozellikler']['beden'] = str(value)
                elif purpose in ['brand', 'marka']:
                    enriched['onemli_ozellikler']['marka'] = str(value)
        
        # Seçme nedeni yoksa oluştur
        if not enriched.get('secme_nedeni'):
            enriched['secme_nedeni'] = self._generate_selection_reason(item)
        
        return enriched
    
    def _generate_selection_reason(self, item: Dict[str, Any]) -> str:
        """Seçim nedeni oluştur"""
        reasons = []
        
        # Filtrelerden sebepler
        filters = self.output_requirements.get('filters', {})
        if 'color' in filters or 'renk' in filters:
            reasons.append(f"İstenen renk kriterine uygun")
        if 'category' in filters or 'kategori' in filters:
            reasons.append(f"İstenen kategori kriterine uygun")
        
        # Stil tercihlerinden sebepler
        style_prefs = self.output_requirements.get('style_preferences', [])
        if style_prefs:
            reasons.append(f"Stil tercihlerine uygun: {', '.join(style_prefs)}")
        
        if not reasons:
            reasons.append("Kullanıcı isteğine uygun")
        
        return ". ".join(reasons) + "."


