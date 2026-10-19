"""
Öznitelik Tokenizasyonu ve Anlamlandırma Modülü
Her bir özniteliği derinlemesine analiz edip anlamlandırır ve tokenize eder.
"""
import pandas as pd
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter

class AttributeTokenizer:
    """Her bir özniteliği anlamlandırıp tokenize eden sınıf"""
    
    def __init__(self, df: pd.DataFrame, dataset_name: str):
        """
        Args:
            df: Analiz edilecek DataFrame
            dataset_name: Veri seti adı (örn: 'urunler', 'yorumlar')
        """
        self.df = df
        self.dataset_name = dataset_name
        self.tokenized_attributes = {}
        self.semantic_meanings = {}
        
    def tokenize_all_attributes(self) -> Dict[str, Any]:
        """Tüm öznitelikleri tokenize et ve anlamlandır"""
        print(f"📊 {self.dataset_name} veri setindeki öznitelikler tokenize ediliyor...")
        
        for col in self.df.columns:
            print(f"  → {col} özniteliği işleniyor...")
            self.tokenized_attributes[col] = self._tokenize_attribute(col)
            self.semantic_meanings[col] = self._extract_semantic_meaning(col)
        
        print(f"✓ {len(self.tokenized_attributes)} öznitelik tokenize edildi")
        return {
            'tokenized': self.tokenized_attributes,
            'semantic_meanings': self.semantic_meanings
        }
    
    def _tokenize_attribute(self, column_name: str) -> Dict[str, Any]:
        """Bir özniteliği detaylı şekilde tokenize et"""
        series = self.df[column_name].dropna()
        
        if len(series) == 0:
            return {
                'type': 'empty',
                'tokens': [],
                'token_count': 0,
                'structure': 'boş_sütun'
            }
        
        # Veri tipine göre tokenizasyon
        if pd.api.types.is_numeric_dtype(series):
            return self._tokenize_numeric(series, column_name)
        elif pd.api.types.is_datetime64_any_dtype(series):
            return self._tokenize_datetime(series, column_name)
        elif pd.api.types.is_bool_dtype(series):
            return self._tokenize_boolean(series, column_name)
        else:
            return self._tokenize_text(series, column_name)
    
    def _tokenize_numeric(self, series: pd.Series, column_name: str) -> Dict[str, Any]:
        """Sayısal özniteliği tokenize et"""
        tokens = []
        
        # İstatistiksel tokenlar
        tokens.append(f"min:{series.min()}")
        tokens.append(f"max:{series.max()}")
        tokens.append(f"mean:{series.mean():.2f}")
        tokens.append(f"median:{series.median():.2f}")
        tokens.append(f"std:{series.std():.2f}")
        
        # Değer aralıkları
        if series.min() != series.max():
            q25 = series.quantile(0.25)
            q75 = series.quantile(0.75)
            tokens.append(f"q25:{q25:.2f}")
            tokens.append(f"q75:{q75:.2f}")
        
        # Benzersiz değer sayısı
        unique_count = series.nunique()
        tokens.append(f"unique_count:{unique_count}")
        
        # Örnek değerler
        sample_values = series.head(10).tolist()
        for val in sample_values:
            tokens.append(f"value:{val}")
        
        return {
            'type': 'numeric',
            'tokens': tokens,
            'token_count': len(tokens),
            'structure': f"sayısal_aralık_{series.min()}_to_{series.max()}",
            'statistics': {
                'min': float(series.min()),
                'max': float(series.max()),
                'mean': float(series.mean()),
                'median': float(series.median()),
                'std': float(series.std()),
                'unique_count': int(unique_count)
            }
        }
    
    def _tokenize_datetime(self, series: pd.Series, column_name: str) -> Dict[str, Any]:
        """Tarih/saat özniteliğini tokenize et"""
        tokens = []
        
        # Tarih aralığı
        tokens.append(f"start_date:{series.min()}")
        tokens.append(f"end_date:{series.max()}")
        
        # Tarih bileşenleri
        if hasattr(series.dt, 'year'):
            tokens.append(f"year_range:{series.dt.year.min()}_to_{series.dt.year.max()}")
            tokens.append(f"month_range:{series.dt.month.min()}_to_{series.dt.month.max()}")
            tokens.append(f"day_range:{series.dt.day.min()}_to_{series.dt.day.max()}")
        
        # Örnek tarihler
        sample_dates = series.head(5).astype(str).tolist()
        for date in sample_dates:
            tokens.append(f"date:{date}")
        
        return {
            'type': 'datetime',
            'tokens': tokens,
            'token_count': len(tokens),
            'structure': f"tarih_aralığı_{series.min()}_to_{series.max()}",
            'date_range': {
                'start': str(series.min()),
                'end': str(series.max())
            }
        }
    
    def _tokenize_boolean(self, series: pd.Series, column_name: str) -> Dict[str, Any]:
        """Boolean özniteliğini tokenize et"""
        tokens = []
        
        value_counts = series.value_counts()
        true_count = value_counts.get(True, 0)
        false_count = value_counts.get(False, 0)
        
        tokens.append(f"true_count:{true_count}")
        tokens.append(f"false_count:{false_count}")
        tokens.append(f"true_ratio:{true_count/len(series):.2f}")
        tokens.append(f"false_ratio:{false_count/len(series):.2f}")
        
        return {
            'type': 'boolean',
            'tokens': tokens,
            'token_count': len(tokens),
            'structure': 'boolean_değer',
            'distribution': {
                'true': int(true_count),
                'false': int(false_count)
            }
        }
    
    def _tokenize_text(self, series: pd.Series, column_name: str) -> Dict[str, Any]:
        """Metin özniteliğini tokenize et"""
        tokens = []
        str_series = series.astype(str)
        
        # Uzunluk istatistikleri
        lengths = str_series.str.len()
        tokens.append(f"avg_length:{lengths.mean():.0f}")
        tokens.append(f"min_length:{lengths.min()}")
        tokens.append(f"max_length:{lengths.max()}")
        
        # Kelime sayısı (boşluklara göre)
        word_counts = str_series.str.split().str.len()
        tokens.append(f"avg_words:{word_counts.mean():.1f}")
        
        # Benzersiz değerler
        unique_count = series.nunique()
        tokens.append(f"unique_count:{unique_count}")
        
        # En sık kullanılan değerler
        value_counts = series.value_counts().head(10)
        for val, count in value_counts.items():
            if pd.notna(val) and str(val).strip():
                # Değeri tokenize et (özel karakterleri temizle)
                clean_val = re.sub(r'[^\w\s-]', '', str(val))[:50]  # İlk 50 karakter
                tokens.append(f"frequent_value:{clean_val}:{count}")
        
        # Örnek değerler
        sample_values = series.head(10).tolist()
        for val in sample_values:
            if pd.notna(val) and str(val).strip():
                clean_val = re.sub(r'[^\w\s-]', '', str(val))[:50]
                tokens.append(f"sample_value:{clean_val}")
        
        # Özel pattern'ler (URL, email, vs.)
        if str_series.str.contains(r'http', case=False, na=False).any():
            tokens.append("contains_urls:true")
        if str_series.str.contains(r'@', case=False, na=False).any():
            tokens.append("contains_emails:true")
        if str_series.str.contains(r'\d{4,}', case=False, na=False).any():
            tokens.append("contains_numbers:true")
        
        return {
            'type': 'text',
            'tokens': tokens,
            'token_count': len(tokens),
            'structure': f"metin_uzunluk_{lengths.mean():.0f}_chars",
            'text_stats': {
                'avg_length': float(lengths.mean()),
                'min_length': int(lengths.min()),
                'max_length': int(lengths.max()),
                'avg_words': float(word_counts.mean()),
                'unique_count': int(unique_count)
            }
        }
    
    def _extract_semantic_meaning(self, column_name: str) -> Dict[str, Any]:
        """Özniteliğin semantik anlamını çıkar"""
        series = self.df[column_name].dropna()
        
        # Sütun adından anlam çıkarma
        col_lower = column_name.lower()
        
        semantic_info = {
            'attribute_name': column_name,
            'likely_purpose': self._infer_purpose(col_lower, series),
            'importance_level': self._infer_importance(series),
            'data_quality': self._assess_quality(series),
            'relationships': self._infer_relationships(col_lower)
        }
        
        return semantic_info
    
    def _infer_purpose(self, col_name: str, series: pd.Series) -> str:
        """Özniteliğin muhtemel amacını çıkar"""
        # Anahtar kelime eşleştirme
        if any(word in col_name for word in ['id', 'numara', 'no', 'link']):
            return 'identifier'
        elif any(word in col_name for word in ['fiyat', 'price', 'tutar', 'ücret']):
            return 'price'
        elif any(word in col_name for word in ['renk', 'color', 'colour']):
            return 'color'
        elif any(word in col_name for word in ['kategori', 'category', 'kat', 'tip']):
            return 'category'
        elif any(word in col_name for word in ['ad', 'name', 'isim', 'tanım', 'description']):
            return 'name_description'
        elif any(word in col_name for word in ['yorum', 'comment', 'review', 'değerlendirme']):
            return 'review_text'
        elif any(word in col_name for word in ['yıldız', 'star', 'rating', 'puan']):
            return 'rating'
        elif any(word in col_name for word in ['görsel', 'image', 'resim', 'foto']):
            return 'image_url'
        elif any(word in col_name for word in ['tarih', 'date', 'zaman', 'time']):
            return 'date_time'
        elif any(word in col_name for word in ['beden', 'size', 'ölçü']):
            return 'size'
        elif any(word in col_name for word in ['marka', 'brand']):
            return 'brand'
        else:
            return 'general_attribute'
    
    def _infer_importance(self, series: pd.Series) -> str:
        """Özniteliğin önem seviyesini belirle"""
        null_ratio = series.isnull().sum() / len(self.df)
        unique_ratio = series.nunique() / len(series.dropna()) if len(series.dropna()) > 0 else 0
        
        if null_ratio < 0.1 and unique_ratio > 0.5:
            return 'high'  # Düşük null, yüksek çeşitlilik
        elif null_ratio < 0.3:
            return 'medium'
        else:
            return 'low'
    
    def _assess_quality(self, series: pd.Series) -> Dict[str, Any]:
        """Veri kalitesini değerlendir"""
        null_count = series.isnull().sum()
        null_ratio = null_count / len(self.df)
        
        # Tekrar eden değerler
        if len(series.dropna()) > 0:
            duplicate_ratio = (len(series) - series.nunique()) / len(series.dropna())
        else:
            duplicate_ratio = 0
        
        return {
            'null_count': int(null_count),
            'null_ratio': float(null_ratio),
            'completeness': float(1 - null_ratio),
            'duplicate_ratio': float(duplicate_ratio),
            'quality_score': float((1 - null_ratio) * (1 - min(duplicate_ratio, 0.5)))
        }
    
    def _infer_relationships(self, col_name: str) -> List[str]:
        """Diğer özniteliklerle olası ilişkileri çıkar"""
        relationships = []
        
        # İlişki ipuçları
        if 'urun' in col_name or 'product' in col_name:
            relationships.append('product_related')
        if 'yorum' in col_name or 'review' in col_name:
            relationships.append('review_related')
        if 'link' in col_name or 'url' in col_name:
            relationships.append('reference_link')
        if 'id' in col_name:
            relationships.append('foreign_key_candidate')
        
        return relationships






