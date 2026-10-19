import pandas as pd
import json
from typing import Dict, List, Any, Optional
from .attribute_tokenizer import AttributeTokenizer
from .attribute_categorizer import AttributeCategorizer
from .attribute_trainer import AttributeTrainer
from .smart_query_parser import SmartQueryParser

class DataProcessor:
    def __init__(self, urunler_path: str, yorumlar_path: str):
        self.urunler_path = urunler_path
        self.yorumlar_path = yorumlar_path
        self.urunler_df = None
        self.yorumlar_df = None
        self.urunler_attributes = {}
        self.yorumlar_attributes = {}
        
        # Yeni mimari bileşenleri
        self.urunler_tokenizer = None
        self.yorumlar_tokenizer = None
        self.urunler_categorizer = None
        self.yorumlar_categorizer = None
        self.urunler_trainer = None
        self.yorumlar_trainer = None
        
        # Tokenize ve öğrenilmiş veriler
        self.urunler_tokenized = {}
        self.yorumlar_tokenized = {}
        self.urunler_categories = {}
        self.yorumlar_categories = {}
        self.urunler_learned_patterns = {}
        self.yorumlar_learned_patterns = {}
        
        # Akıllı sorgu parser (veri bilimi tabanlı)
        self.smart_parser = None
        
    def load_data(self):
        """Veri setlerini yükle"""
        print("Veri setleri yükleniyor...")
        self.urunler_df = pd.read_excel(self.urunler_path)
        self.yorumlar_df = pd.read_excel(self.yorumlar_path)
        print(f"✓ {len(self.urunler_df)} ürün yüklendi")
        print(f"✓ {len(self.yorumlar_df)} yorum yüklendi")
        
    def analyze_attributes(self):
        """Tüm öznitelikleri analiz et ve yapılarını çıkar - YENİ MİMARİ"""
        print("=" * 60)
        print("ADIM 1: ÖZNİTELİKLERİ TOKENİZE ET VE ANLAMLANDIR")
        print("=" * 60)
        
        # 1. Tokenizasyon ve anlamlandırma
        self.urunler_tokenizer = AttributeTokenizer(self.urunler_df, 'urunler')
        urunler_tokenized_result = self.urunler_tokenizer.tokenize_all_attributes()
        self.urunler_tokenized = urunler_tokenized_result['tokenized']
        self.urunler_semantic = urunler_tokenized_result['semantic_meanings']
        
        self.yorumlar_tokenizer = AttributeTokenizer(self.yorumlar_df, 'yorumlar')
        yorumlar_tokenized_result = self.yorumlar_tokenizer.tokenize_all_attributes()
        self.yorumlar_tokenized = yorumlar_tokenized_result['tokenized']
        self.yorumlar_semantic = yorumlar_tokenized_result['semantic_meanings']
        
        print("\n" + "=" * 60)
        print("ADIM 2: ÖZNİTELİKLERİ KATEGORİLERE AYIR")
        print("=" * 60)
        
        # 2. Kategorileştirme
        self.urunler_categorizer = AttributeCategorizer(
            self.urunler_tokenized, 
            self.urunler_semantic
        )
        self.urunler_categories = self.urunler_categorizer.categorize_all()
        
        self.yorumlar_categorizer = AttributeCategorizer(
            self.yorumlar_tokenized,
            self.yorumlar_semantic
        )
        self.yorumlar_categories = self.yorumlar_categorizer.categorize_all()
        
        print("\n" + "=" * 60)
        print("ADIM 3: HER KATEGORİ İÇİN ÖĞRENME YAP")
        print("=" * 60)
        
        # 3. Öğrenme
        self.urunler_trainer = AttributeTrainer(
            self.urunler_df,
            self.urunler_tokenized,
            self.urunler_semantic,
            self.urunler_categories
        )
        self.urunler_learned_patterns = self.urunler_trainer.train_all_categories()
        
        self.yorumlar_trainer = AttributeTrainer(
            self.yorumlar_df,
            self.yorumlar_tokenized,
            self.yorumlar_semantic,
            self.yorumlar_categories
        )
        self.yorumlar_learned_patterns = self.yorumlar_trainer.train_all_categories()
        
        print("\n" + "=" * 60)
        print("ADIM 4: AKILLI SORGU PARSER OLUŞTURULUYOR")
        print("=" * 60)
        
        # 4. Akıllı sorgu parser'ı başlat (veri bilimi tabanlı)
        self.smart_parser = SmartQueryParser(
            urunler_df=self.urunler_df,
            learned_patterns=self.urunler_learned_patterns,
            semantic_meanings=self.urunler_semantic
        )
        
        print("\n" + "=" * 60)
        print("✓ TÜM ADIMLAR TAMAMLANDI")
        print("=" * 60)
        
        # Eski format için uyumluluk
        for col in self.urunler_df.columns:
            self.urunler_attributes[col] = {
                'dtype': str(self.urunler_df[col].dtype),
                'null_count': int(self.urunler_df[col].isnull().sum()),
                'null_percentage': float((self.urunler_df[col].isnull().sum() / len(self.urunler_df)) * 100),
                'unique_count': int(self.urunler_df[col].nunique()),
                'sample_values': self.urunler_df[col].dropna().head(5).tolist() if len(self.urunler_df[col].dropna()) > 0 else [],
                'description': self._describe_column(self.urunler_df[col])
            }
        
        for col in self.yorumlar_df.columns:
            self.yorumlar_attributes[col] = {
                'dtype': str(self.yorumlar_df[col].dtype),
                'null_count': int(self.yorumlar_df[col].isnull().sum()),
                'null_percentage': float((self.yorumlar_df[col].isnull().sum() / len(self.yorumlar_df)) * 100),
                'unique_count': int(self.yorumlar_df[col].nunique()),
                'sample_values': self.yorumlar_df[col].dropna().head(5).tolist() if len(self.yorumlar_df[col].dropna()) > 0 else [],
                'description': self._describe_column(self.yorumlar_df[col])
            }
    
    def _describe_column(self, series: pd.Series) -> str:
        """Sütunun yapısını açıkla"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return "Boş sütun"
        
        if pd.api.types.is_numeric_dtype(series):
            return f"Numeric: min={non_null.min()}, max={non_null.max()}, mean={non_null.mean():.2f}"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return f"Date: range from {non_null.min()} to {non_null.max()}"
        else:
            # String sütunlar için
            str_series = non_null.astype(str)
            avg_len = str_series.str.len().mean()
            max_len = str_series.str.len().max()
            return f"Text: average length {avg_len:.0f} chars, max {max_len} chars"
    
    def tokenize_attributes(self) -> str:
        """Tüm öznitelikleri LLM için tokenize et - Yeni mimari özeti"""
        summary = {
            'urunler': {
                'tokenized': self.urunler_tokenized,
                'semantic': self.urunler_semantic,
                'categories': self.urunler_categories,
                'learned_patterns': self.urunler_learned_patterns
            },
            'yorumlar': {
                'tokenized': self.yorumlar_tokenized,
                'semantic': self.yorumlar_semantic,
                'categories': self.yorumlar_categories,
                'learned_patterns': self.yorumlar_learned_patterns
            }
        }
        return json.dumps(summary, ensure_ascii=False, indent=2, default=str)
    
    def get_tokenized_data(self) -> Dict[str, Any]:
        """Tokenize edilmiş verileri getir"""
        return {
            'urunler': {
                'tokenized': self.urunler_tokenized,
                'semantic': self.urunler_semantic,
                'categories': self.urunler_categories,
                'learned_patterns': self.urunler_learned_patterns
            },
            'yorumlar': {
                'tokenized': self.yorumlar_tokenized,
                'semantic': self.yorumlar_semantic,
                'categories': self.yorumlar_categories,
                'learned_patterns': self.yorumlar_learned_patterns
            }
        }
    
    def _parse_user_query_for_filters(self, user_query: str) -> Dict[str, Any]:
        """Kullanıcı sorgusundan renk ve kategori filtrelerini çıkarır - VERİ BİLİMİ TABANLI"""
        # Smart parser her zaman initialize() sonrası hazır olmalı
        if self.smart_parser is None:
            raise ValueError("Smart parser henüz başlatılmamış. Lütfen önce initialize() metodunu çağırın.")
        
        # Veri bilimi tabanlı akıllı parsing
        filters = self.smart_parser.parse_query(user_query)
        
        # Confidence bilgisini logla (debug için)
        if filters.get("confidence"):
            if filters["renk"]:
                print(f"  🎨 Renk tespit edildi: '{filters['renk']}' (confidence: {filters['confidence']['renk']:.2f})")
            if filters["kategori"]:
                print(f"  📂 Kategori tespit edildi: '{filters['kategori']}' (confidence: {filters['confidence']['kategori']:.2f})")
        
        return filters
    
    def get_product_context(self, product_id: Optional[str] = None, limit: int = 50, user_query: Optional[str] = None) -> List[Dict]:
        """Belirli bir ürün veya tüm ürünler için context oluştur
        
        Args:
            product_id: Belirli bir ürün ID'si
            limit: Maksimum ürün sayısı
            user_query: Kullanıcı sorgusu (filtreleme için kullanılır)
        """
        if product_id:
            # İlk sütunun ID olduğunu varsayıyoruz, veya urun_linki sütununu kullan
            if 'urun_linki' in self.urunler_df.columns:
                product = self.urunler_df[self.urunler_df['urun_linki'] == product_id]
            else:
                product = self.urunler_df[self.urunler_df.iloc[:, 0] == product_id]
            
            if product.empty:
                return []
            return product.to_dict('records')
        
        df_filtered = self.urunler_df.copy()

        if user_query:
            filters = self._parse_user_query_for_filters(user_query)
            
            # Renk filtresi - Fuzzy matching ile bulunan renk
            if filters.get("renk"):
                matched_color = filters["renk"]
                # Tüm renk sütunlarında ara
                color_columns = [col for col in df_filtered.columns 
                               if 'renk' in col.lower() or 'color' in col.lower()]
                
                if color_columns:
                    # Normalize edilmiş renk ile de eşleştir
                    color_mask = pd.Series([False] * len(df_filtered))
                    for col in color_columns:
                        col_mask = df_filtered[col].astype(str).str.lower().str.contains(
                            matched_color.lower(), case=False, na=False, regex=False
                        )
                        color_mask = color_mask | col_mask
                    
                    df_filtered = df_filtered[color_mask]
            
            # Kategori filtresi - Fuzzy matching ile bulunan kategori
            if filters.get("kategori"):
                matched_category = filters["kategori"]
                # Tüm kategori sütunlarında ara
                category_columns = [col for col in df_filtered.columns 
                                  if 'kategori' in col.lower() or 'category' in col.lower() or 'kat' in col.lower()]
                
                if category_columns:
                    # Normalize edilmiş kategori ile de eşleştir
                    category_mask = pd.Series([False] * len(df_filtered))
                    for col in category_columns:
                        col_mask = df_filtered[col].astype(str).str.lower().str.contains(
                            matched_category.lower(), case=False, na=False, regex=False
                        )
                        category_mask = category_mask | col_mask
                    
                    df_filtered = df_filtered[category_mask]
            
            # Anahtar kelime filtresi (ürün tanımı veya adı içinde)
            if filters["query_keywords"]:
                keyword_pattern = "|".join(filters["query_keywords"])
                df_filtered = df_filtered[
                    df_filtered.apply(lambda row: row.astype(str).str.contains(keyword_pattern, case=False, na=False).any(), axis=1)
                ]

        # Eğer filtreleme sonucu boşsa, tüm ürünlerden al (fallback)
        if df_filtered.empty:
            df_filtered = self.urunler_df.copy()
            print("Uyarı: Filtreleme sonucu boş, tüm ürünlerden seçim yapılıyor.")

        # Limit uygula
        df_subset = df_filtered.sample(min(len(df_filtered), limit), random_state=42) if not df_filtered.empty else pd.DataFrame()
        return df_subset.to_dict('records')
    
    def get_reviews_context(self, product_link: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Ürüne ait yorumları getir"""
        if product_link:
            # Urun Linki sütununu kullan
            if 'Urun Linki' in self.yorumlar_df.columns:
                reviews = self.yorumlar_df[self.yorumlar_df['Urun Linki'] == product_link]
            else:
                reviews = self.yorumlar_df[self.yorumlar_df.iloc[:, 0] == product_link]
            
            # Limit uygula
            reviews = reviews.head(limit)
            return reviews.to_dict('records')
        
        # Tüm yorumlar için limit uygula
        df_subset = self.yorumlar_df.head(limit)
        return df_subset.to_dict('records')
    
    def get_products_with_reviews(self, limit: int = 50) -> Dict[str, Any]:
        """Ürünleri ve ilgili yorumlarını birlikte getir"""
        products = self.get_product_context(limit=limit)
        result = []
        
        for product in products:
            product_link = product.get('urun_linki', '')
            if product_link:
                reviews = self.get_reviews_context(product_link=product_link, limit=10)
                product_with_reviews = {
                    'product': product,
                    'reviews': reviews,
                    'review_count': len(reviews)
                }
                result.append(product_with_reviews)
            else:
                result.append({
                    'product': product,
                    'reviews': [],
                    'review_count': 0
                })
        
        return result



