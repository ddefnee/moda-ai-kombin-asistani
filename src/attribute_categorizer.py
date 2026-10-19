"""
Öznitelik Kategorileştirme Modülü
Öznitelikleri yapılarına göre kategorilere ayırır.
"""
from typing import Dict, List, Any, Set
from collections import defaultdict

class AttributeCategorizer:
    """Öznitelikleri yapılarına göre kategorilere ayıran sınıf"""
    
    def __init__(self, tokenized_attributes: Dict[str, Any], semantic_meanings: Dict[str, Any]):
        """
        Args:
            tokenized_attributes: Tokenize edilmiş öznitelikler
            semantic_meanings: Semantik anlamlar
        """
        self.tokenized_attributes = tokenized_attributes
        self.semantic_meanings = semantic_meanings
        self.categories = defaultdict(list)
        
    def categorize_all(self) -> Dict[str, List[str]]:
        """Tüm öznitelikleri kategorilere ayır"""
        print("📂 Öznitelikler kategorilere ayrılıyor...")
        
        for attr_name in self.tokenized_attributes.keys():
            category = self._determine_category(attr_name)
            self.categories[category].append(attr_name)
        
        print(f"✓ {len(self.categories)} kategori oluşturuldu")
        for cat, attrs in self.categories.items():
            print(f"  → {cat}: {len(attrs)} öznitelik")
        
        return dict(self.categories)
    
    def _determine_category(self, attr_name: str) -> str:
        """Bir özniteliğin kategorisini belirle"""
        token_data = self.tokenized_attributes.get(attr_name, {})
        semantic = self.semantic_meanings.get(attr_name, {})
        
        attr_type = token_data.get('type', 'unknown')
        purpose = semantic.get('likely_purpose', 'general_attribute')
        
        # Tip ve amaç kombinasyonuna göre kategori belirleme
        if attr_type == 'numeric':
            if purpose == 'price':
                return 'numeric_price'
            elif purpose == 'rating':
                return 'numeric_rating'
            elif purpose == 'size':
                return 'numeric_size'
            else:
                return 'numeric_general'
        
        elif attr_type == 'text':
            if purpose == 'identifier':
                return 'text_identifier'
            elif purpose == 'name_description':
                return 'text_name_description'
            elif purpose == 'review_text':
                return 'text_review'
            elif purpose == 'color':
                return 'text_color'
            elif purpose == 'category':
                return 'text_category'
            elif purpose == 'brand':
                return 'text_brand'
            elif purpose == 'image_url':
                return 'text_url'
            else:
                return 'text_general'
        
        elif attr_type == 'datetime':
            return 'datetime_temporal'
        
        elif attr_type == 'boolean':
            return 'boolean_flag'
        
        else:
            return 'unknown'






