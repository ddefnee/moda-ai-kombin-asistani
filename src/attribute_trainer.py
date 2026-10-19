"""
Öznitelik Öğrenme Modülü
Her bir öznitelik kategorisine göre öğrenme/pattern çıkarma işlemleri yapar.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import re

class AttributeTrainer:
    """Öznitelik kategorilerine göre öğrenme yapan sınıf"""
    
    def __init__(self, df: pd.DataFrame, tokenized_attributes: Dict[str, Any], 
                 semantic_meanings: Dict[str, Any], categories: Dict[str, List[str]]):
        """
        Args:
            df: Veri DataFrame'i
            tokenized_attributes: Tokenize edilmiş öznitelikler
            semantic_meanings: Semantik anlamlar
            categories: Kategorilere ayrılmış öznitelikler
        """
        self.df = df
        self.tokenized_attributes = tokenized_attributes
        self.semantic_meanings = semantic_meanings
        self.categories = categories
        self.learned_patterns = {}
        self.category_models = {}
        
    def train_all_categories(self) -> Dict[str, Any]:
        """Tüm kategoriler için öğrenme yap"""
        print("🎓 Öznitelik kategorileri öğreniliyor...")
        
        for category, attributes in self.categories.items():
            print(f"  → {category} kategorisi öğreniliyor ({len(attributes)} öznitelik)...")
            self.learned_patterns[category] = self._train_category(category, attributes)
        
        print(f"✓ {len(self.learned_patterns)} kategori için öğrenme tamamlandı")
        return self.learned_patterns
    
    def _train_category(self, category: str, attributes: List[str]) -> Dict[str, Any]:
        """Bir kategori için öğrenme yap"""
        if category.startswith('numeric_'):
            return self._train_numeric_category(attributes)
        elif category.startswith('text_'):
            return self._train_text_category(category, attributes)
        elif category.startswith('datetime_'):
            return self._train_datetime_category(attributes)
        elif category.startswith('boolean_'):
            return self._train_boolean_category(attributes)
        else:
            return self._train_general_category(attributes)
    
    def _train_numeric_category(self, attributes: List[str]) -> Dict[str, Any]:
        """Sayısal kategori için öğrenme"""
        patterns = {}
        
        for attr in attributes:
            series = self.df[attr].dropna()
            
            if len(series) == 0:
                continue
            
            patterns[attr] = {
                'distribution': {
                    'mean': float(series.mean()),
                    'median': float(series.median()),
                    'std': float(series.std()),
                    'min': float(series.min()),
                    'max': float(series.max()),
                    'q25': float(series.quantile(0.25)),
                    'q75': float(series.quantile(0.75))
                },
                'value_ranges': self._extract_value_ranges(series),
                'outliers': self._detect_outliers(series),
                'normalization_params': {
                    'min': float(series.min()),
                    'max': float(series.max()),
                    'mean': float(series.mean()),
                    'std': float(series.std())
                }
            }
        
        return {
            'category_type': 'numeric',
            'patterns': patterns,
            'common_behaviors': self._find_common_numeric_behaviors(patterns)
        }
    
    def _train_text_category(self, category: str, attributes: List[str]) -> Dict[str, Any]:
        """Metin kategori için öğrenme"""
        patterns = {}
        
        for attr in attributes:
            series = self.df[attr].dropna().astype(str)
            
            if len(series) == 0:
                continue
            
            if category == 'text_color':
                patterns[attr] = self._learn_color_patterns(series)
            elif category == 'text_category':
                patterns[attr] = self._learn_category_patterns(series)
            elif category == 'text_brand':
                patterns[attr] = self._learn_brand_patterns(series)
            elif category == 'text_review':
                patterns[attr] = self._learn_review_patterns(series)
            elif category == 'text_name_description':
                patterns[attr] = self._learn_name_description_patterns(series)
            else:
                patterns[attr] = self._learn_general_text_patterns(series)
        
        return {
            'category_type': 'text',
            'patterns': patterns,
            'common_behaviors': self._find_common_text_behaviors(patterns)
        }
    
    def _train_datetime_category(self, attributes: List[str]) -> Dict[str, Any]:
        """Tarih/saat kategori için öğrenme"""
        patterns = {}
        
        for attr in attributes:
            series = pd.to_datetime(self.df[attr], errors='coerce').dropna()
            
            if len(series) == 0:
                continue
            
            patterns[attr] = {
                'temporal_range': {
                    'start': str(series.min()),
                    'end': str(series.max()),
                    'span_days': (series.max() - series.min()).days
                },
                'temporal_patterns': {
                    'year_distribution': series.dt.year.value_counts().to_dict(),
                    'month_distribution': series.dt.month.value_counts().to_dict(),
                    'day_of_week_distribution': series.dt.dayofweek.value_counts().to_dict()
                },
                'seasonality': self._detect_seasonality(series)
            }
        
        return {
            'category_type': 'datetime',
            'patterns': patterns
        }
    
    def _train_boolean_category(self, attributes: List[str]) -> Dict[str, Any]:
        """Boolean kategori için öğrenme"""
        patterns = {}
        
        for attr in attributes:
            series = self.df[attr].dropna()
            
            if len(series) == 0:
                continue
            
            value_counts = series.value_counts()
            patterns[attr] = {
                'distribution': {
                    'true_count': int(value_counts.get(True, 0)),
                    'false_count': int(value_counts.get(False, 0)),
                    'true_ratio': float(value_counts.get(True, 0) / len(series)),
                    'false_ratio': float(value_counts.get(False, 0) / len(series))
                }
            }
        
        return {
            'category_type': 'boolean',
            'patterns': patterns
        }
    
    def _train_general_category(self, attributes: List[str]) -> Dict[str, Any]:
        """Genel kategori için öğrenme"""
        patterns = {}
        
        for attr in attributes:
            series = self.df[attr].dropna()
            patterns[attr] = {
                'unique_count': int(series.nunique()),
                'null_ratio': float(series.isnull().sum() / len(self.df)),
                'sample_values': series.head(10).tolist()
            }
        
        return {
            'category_type': 'general',
            'patterns': patterns
        }
    
    # Yardımcı metodlar
    def _extract_value_ranges(self, series: pd.Series) -> List[Dict[str, float]]:
        """Değer aralıklarını çıkar"""
        ranges = []
        
        # Eşit genişlikte aralıklar
        if series.min() != series.max():
            num_bins = min(10, series.nunique())
            bins = pd.cut(series, bins=num_bins, duplicates='drop')
            bin_counts = bins.value_counts()
            
            for interval, count in bin_counts.head(5).items():
                if pd.notna(interval):
                    ranges.append({
                        'min': float(interval.left),
                        'max': float(interval.right),
                        'count': int(count),
                        'ratio': float(count / len(series))
                    })
        
        return ranges
    
    def _detect_outliers(self, series: pd.Series) -> Dict[str, Any]:
        """Aykırı değerleri tespit et"""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        
        return {
            'count': int(len(outliers)),
            'ratio': float(len(outliers) / len(series)),
            'lower_bound': float(lower_bound),
            'upper_bound': float(upper_bound)
        }
    
    def _learn_color_patterns(self, series: pd.Series) -> Dict[str, Any]:
        """Renk pattern'lerini öğren - VERİ SETİNDEN ÖĞRENİLEN RENK GRUPLARI"""
        color_counts = series.value_counts().head(20)
        
        # Veri setinden renk gruplarını otomatik öğren
        # Renk isimlerinden ortak kelimeleri çıkararak gruplar oluştur
        color_groups = self._learn_color_groups_from_data(series)
        
        grouped_colors = defaultdict(int)
        for color, count in color_counts.items():
            color_lower = str(color).lower()
            matched = False
            for group, group_colors in color_groups.items():
                if any(group_color.lower() in color_lower or color_lower in group_color.lower() 
                       for group_color in group_colors):
                    grouped_colors[group] += count
                    matched = True
                    break
            if not matched:
                grouped_colors['other'] += count
        
        return {
            'unique_colors': int(series.nunique()),
            'top_colors': color_counts.to_dict(),
            'color_groups': dict(grouped_colors),
            'learned_color_groups': color_groups,  # Öğrenilmiş renk grupları
            'most_common': str(color_counts.index[0]) if len(color_counts) > 0 else None
        }
    
    def _learn_color_groups_from_data(self, series: pd.Series) -> Dict[str, List[str]]:
        """Veri setinden renk gruplarını otomatik öğren - CLUSTERING TABANLI"""
        color_groups = defaultdict(list)
        all_colors = series.dropna().unique()
        
        # Renk isimlerinden ortak kelimeleri çıkar (clustering benzeri yaklaşım)
        color_words = defaultdict(list)  # Her kelime için hangi renklerde geçiyor
        
        for color in all_colors:
            if pd.isna(color):
                continue
            
            color_str = str(color).lower().strip()
            words = re.findall(r'\b\w+\b', color_str)
            
            for word in words:
                if len(word) > 2:  # Kısa kelimeleri atla
                    color_words[word].append(color_str)
        
        # En sık geçen kelimeleri bul (renk gruplarını temsil eden kelimeler)
        word_frequencies = {word: len(colors) for word, colors in color_words.items()}
        common_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)[:30]
        
        # Renk tonlarını tespit et (veri setinden öğrenilen)
        tone_keywords = self._extract_tone_keywords_from_colors(all_colors)
        
        # Her rengi gruplara ayır
        for color in all_colors:
            if pd.isna(color):
                continue
            
            color_str = str(color).lower().strip()
            words = set(re.findall(r'\b\w+\b', color_str))
            
            # 1. Ton grupları (açık/koyu) - veri setinden öğrenilen
            matched_tone = None
            for tone, tone_words in tone_keywords.items():
                if any(tw in words for tw in tone_words):
                    matched_tone = tone
                    color_groups[tone].append(color_str)
                    break
            
            # 2. Ana renk grupları - veri setindeki ortak kelimelerden
            if not matched_tone:
                # En sık geçen kelimeleri kullanarak grupla
                matched_group = None
                for word, freq in common_words:
                    if word in words and freq >= 3:  # En az 3 renkte geçen kelimeler
                        # Kelimeye göre grup adı oluştur
                        group_name = f"color_{word}"
                        color_groups[group_name].append(color_str)
                        matched_group = group_name
                        break
                
                if not matched_group:
                    color_groups['other'].append(color_str)
        
        # Genel gruplar oluştur (warm/cool/neutral) - veri setinden öğrenilen pattern'lere göre
        general_groups = self._create_general_color_groups(color_groups)
        color_groups.update(general_groups)
        
        return dict(color_groups)
    
    def _extract_tone_keywords_from_colors(self, all_colors: np.ndarray) -> Dict[str, List[str]]:
        """Veri setindeki renklerden ton kelimelerini çıkar - TAMAMEN VERİ SETİNDEN ÖĞRENİLEN (SEED YOK)"""
        tone_keywords = {
            'light': [],
            'dark': []
        }
        
        # Veri setindeki renklerden ton kelimelerini otomatik öğren
        # Clustering benzeri yaklaşım: Renk isimlerindeki kelimeleri analiz et
        # ve benzer renklerde geçen kelimeleri grupla
        
        # Tüm renklerdeki kelimeleri topla
        all_color_words = defaultdict(list)  # Her kelime için hangi renklerde geçiyor
        word_frequencies = defaultdict(int)
        
        for color in all_colors:
            if pd.isna(color):
                continue
            
            color_str = str(color).lower().strip()
            words = re.findall(r'\b\w+\b', color_str)
            
            for word in words:
                if len(word) > 2:
                    all_color_words[word].append(color_str)
                    word_frequencies[word] += 1
        
        # Renk isimlerindeki kelimeleri analiz et
        # Benzer renklerde birlikte geçen kelimeleri bul (co-occurrence)
        word_cooccurrence = defaultdict(lambda: defaultdict(int))
        
        for color in all_colors:
            if pd.isna(color):
                continue
            
            color_str = str(color).lower().strip()
            words = list(set(re.findall(r'\b\w+\b', color_str)))
            
            # Aynı renk içindeki kelimelerin birlikte geçme sayısını artır
            for i, word1 in enumerate(words):
                if len(word1) > 2:
                    for word2 in words[i+1:]:
                        if len(word2) > 2:
                            word_cooccurrence[word1][word2] += 1
                            word_cooccurrence[word2][word1] += 1
        
        # En sık geçen kelimeleri bul
        top_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)
        
        # Renk isimlerindeki kelime dağılımına göre ton grupları oluştur
        # Basit yaklaşım: En sık geçen kelimeleri iki gruba ayır (light/dark)
        # Daha gelişmiş: Co-occurrence analizi ile benzer kelimeleri grupla
        
        # Co-occurrence matrisine göre kelimeleri iki gruba ayır
        # Her kelime için en çok birlikte geçen kelimeleri bul
        light_candidates = set()
        dark_candidates = set()
        
        # En sık geçen kelimeleri analiz et
        for word, freq in top_words[:50]:  # İlk 50 kelime
            if freq >= 2:  # En az 2 kez geçen kelimeler
                # Bu kelimeyle en çok birlikte geçen kelimeleri bul
                co_words = sorted(word_cooccurrence[word].items(), key=lambda x: x[1], reverse=True)
                
                # Eğer bu kelime başka kelimelerle sık birlikte geçiyorsa
                if co_words and co_words[0][1] >= 2:
                    # Bu kelimeyi ve birlikte geçen kelimeleri aynı gruba ekle
                    # Hangi gruba ekleneceğini, kelimenin mevcut gruplardaki varlığına göre belirle
                    if word in light_candidates or any(co_word in light_candidates for co_word, _ in co_words[:3]):
                        light_candidates.add(word)
                        for co_word, _ in co_words[:3]:
                            light_candidates.add(co_word)
                    elif word in dark_candidates or any(co_word in dark_candidates for co_word, _ in co_words[:3]):
                        dark_candidates.add(word)
                        for co_word, _ in co_words[:3]:
                            dark_candidates.add(co_word)
                    else:
                        # Yeni kelime, frekansına göre gruba ekle
                        if len(light_candidates) <= len(dark_candidates):
                            light_candidates.add(word)
                        else:
                            dark_candidates.add(word)
        
        # Eğer gruplar boşsa, en sık geçen kelimeleri eşit olarak dağıt
        if not light_candidates and not dark_candidates:
            for i, (word, freq) in enumerate(top_words[:40]):
                if freq >= 2:
                    if i % 2 == 0:
                        light_candidates.add(word)
                    else:
                        dark_candidates.add(word)
        
        tone_keywords['light'] = list(light_candidates)[:20]
        tone_keywords['dark'] = list(dark_candidates)[:20]
        
        return tone_keywords
    
    def _create_general_color_groups(self, color_groups: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Genel renk grupları oluştur (warm/cool/neutral) - VERİ SETİNDEN ÖĞRENİLEN PATTERN'LERE GÖRE"""
        general_groups = {
            'warm': [],
            'cool': [],
            'neutral': []
        }
        
        # Veri setindeki tüm renklerden warm/cool/neutral pattern'lerini otomatik öğren
        all_colors = []
        for colors in color_groups.values():
            all_colors.extend(colors)
        
        # Renk isimlerinden ortak kelimeleri çıkar
        warm_words = defaultdict(int)
        cool_words = defaultdict(int)
        neutral_words = defaultdict(int)
        
        # Renk gruplarından warm/cool/neutral pattern'lerini çıkar - TAMAMEN VERİ SETİNDEN ÖĞRENİLEN
        # Clustering benzeri yaklaşım: Renk isimlerindeki kelimeleri analiz et
        # ve benzer renklerde geçen kelimeleri grupla
        
        # Tüm renklerdeki kelimeleri topla
        all_color_words = defaultdict(list)
        word_frequencies = defaultdict(int)
        
        for color in all_colors:
            if pd.isna(color):
                continue
            
            color_str = str(color).lower().strip()
            words = re.findall(r'\b\w+\b', color_str)
            
            for word in words:
                if len(word) > 2:
                    all_color_words[word].append(color_str)
                    word_frequencies[word] += 1
        
        # Renk isimlerindeki kelimelerin birlikte geçme analizi (co-occurrence)
        word_cooccurrence = defaultdict(lambda: defaultdict(int))
        
        for color in all_colors:
            if pd.isna(color):
                continue
            
            color_str = str(color).lower().strip()
            words = list(set(re.findall(r'\b\w+\b', color_str)))
            
            # Aynı renk içindeki kelimelerin birlikte geçme sayısını artır
            for i, word1 in enumerate(words):
                if len(word1) > 2:
                    for word2 in words[i+1:]:
                        if len(word2) > 2:
                            word_cooccurrence[word1][word2] += 1
                            word_cooccurrence[word2][word1] += 1
        
        # Renk gruplarından kelimeleri çıkar
        for group_name, colors in color_groups.items():
            if group_name in ['light', 'dark', 'other']:
                continue
            
            # Her renk için kelimeleri analiz et
            for color in colors:
                color_lower = color.lower()
                words = set(re.findall(r'\b\w+\b', color_lower))
                
                # Tüm kelimeleri frekanslarına göre topla
                for word in words:
                    if len(word) > 2:
                        # Kelimenin hangi grupta olduğunu belirlemek için
                        # co-occurrence analizini kullan
                        # Şimdilik tüm kelimeleri topla, sonra grupla
                        warm_words[word] += 1
                        cool_words[word] += 1
                        neutral_words[word] += 1
        
        # En sık geçen kelimeleri bul
        top_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)
        
        # Co-occurrence analizine göre kelimeleri üç gruba ayır (warm/cool/neutral)
        # Her kelime için en çok birlikte geçen kelimeleri bul
        warm_candidates = set()
        cool_candidates = set()
        neutral_candidates = set()
        
        # En sık geçen kelimeleri analiz et
        for word, freq in top_words[:60]:  # İlk 60 kelime
            if freq >= 2:  # En az 2 kez geçen kelimeler
                # Bu kelimeyle en çok birlikte geçen kelimeleri bul
                co_words = sorted(word_cooccurrence[word].items(), key=lambda x: x[1], reverse=True)
                
                # Eğer bu kelime başka kelimelerle sık birlikte geçiyorsa
                if co_words and co_words[0][1] >= 2:
                    # Bu kelimeyi ve birlikte geçen kelimeleri aynı gruba ekle
                    # Hangi gruba ekleneceğini, kelimenin mevcut gruplardaki varlığına göre belirle
                    if word in warm_candidates or any(co_word in warm_candidates for co_word, _ in co_words[:3]):
                        warm_candidates.add(word)
                        for co_word, _ in co_words[:3]:
                            warm_candidates.add(co_word)
                    elif word in cool_candidates or any(co_word in cool_candidates for co_word, _ in co_words[:3]):
                        cool_candidates.add(word)
                        for co_word, _ in co_words[:3]:
                            cool_candidates.add(co_word)
                    elif word in neutral_candidates or any(co_word in neutral_candidates for co_word, _ in co_words[:3]):
                        neutral_candidates.add(word)
                        for co_word, _ in co_words[:3]:
                            neutral_candidates.add(co_word)
                    else:
                        # Yeni kelime, frekansına göre gruba ekle (round-robin)
                        group_sizes = [len(warm_candidates), len(cool_candidates), len(neutral_candidates)]
                        min_group_idx = group_sizes.index(min(group_sizes))
                        if min_group_idx == 0:
                            warm_candidates.add(word)
                        elif min_group_idx == 1:
                            cool_candidates.add(word)
                        else:
                            neutral_candidates.add(word)
        
        # Eğer gruplar boşsa, en sık geçen kelimeleri eşit olarak dağıt
        if not warm_candidates and not cool_candidates and not neutral_candidates:
            for i, (word, freq) in enumerate(top_words[:60]):
                if freq >= 2:
                    if i % 3 == 0:
                        warm_candidates.add(word)
                    elif i % 3 == 1:
                        cool_candidates.add(word)
                    else:
                        neutral_candidates.add(word)
        
        warm_indicators = list(warm_candidates)[:15]
        cool_indicators = list(cool_candidates)[:15]
        neutral_indicators = list(neutral_candidates)[:15]
        
        # Renkleri genel gruplara ayır
        for group_name, colors in color_groups.items():
            if group_name in ['light', 'dark', 'other']:
                continue
            
            for color in colors:
                color_lower = color.lower()
                words = set(re.findall(r'\b\w+\b', color_lower))
                
                # Warm indicator'ları kontrol et
                if any(indicator in words or indicator in color_lower for indicator in warm_indicators):
                    if color not in general_groups['warm']:
                        general_groups['warm'].append(color)
                # Cool indicator'ları kontrol et
                elif any(indicator in words or indicator in color_lower for indicator in cool_indicators):
                    if color not in general_groups['cool']:
                        general_groups['cool'].append(color)
                # Neutral indicator'ları kontrol et
                elif any(indicator in words or indicator in color_lower for indicator in neutral_indicators):
                    if color not in general_groups['neutral']:
                        general_groups['neutral'].append(color)
        
        return general_groups
    
    def _learn_category_patterns(self, series: pd.Series) -> Dict[str, Any]:
        """Kategori pattern'lerini öğren"""
        category_counts = series.value_counts()
        
        return {
            'unique_categories': int(series.nunique()),
            'top_categories': category_counts.head(20).to_dict(),
            'category_distribution': {
                'most_common': str(category_counts.index[0]) if len(category_counts) > 0 else None,
                'most_common_ratio': float(category_counts.iloc[0] / len(series)) if len(category_counts) > 0 else 0
            }
        }
    
    def _learn_brand_patterns(self, series: pd.Series) -> Dict[str, Any]:
        """Marka pattern'lerini öğren"""
        brand_counts = series.value_counts()
        
        return {
            'unique_brands': int(series.nunique()),
            'top_brands': brand_counts.head(20).to_dict(),
            'brand_concentration': {
                'top_5_ratio': float(brand_counts.head(5).sum() / len(series))
            }
        }
    
    def _learn_review_patterns(self, series: pd.Series) -> Dict[str, Any]:
        """Yorum pattern'lerini öğren - VERİ SETİNDEN ÖĞRENİLEN DUYGU ANALİZİ"""
        lengths = series.str.len()
        
        # Veri setinden duygu kelimelerini öğren (yıldız puanlarına göre)
        positive_words, negative_words = self._learn_sentiment_words_from_data(series)
        
        positive_count = series.str.lower().str.contains('|'.join(positive_words), case=False, na=False).sum() if positive_words else 0
        negative_count = series.str.lower().str.contains('|'.join(negative_words), case=False, na=False).sum() if negative_words else 0
        
        return {
            'avg_length': float(lengths.mean()),
            'length_distribution': {
                'short': int((lengths < 50).sum()),
                'medium': int(((lengths >= 50) & (lengths < 200)).sum()),
                'long': int((lengths >= 200).sum())
            },
            'sentiment_hints': {
                'positive_ratio': float(positive_count / len(series)) if len(series) > 0 else 0.0,
                'negative_ratio': float(negative_count / len(series)) if len(series) > 0 else 0.0,
                'learned_positive_words': positive_words[:50],  # İlk 50 kelime
                'learned_negative_words': negative_words[:50]   # İlk 50 kelime
            }
        }
    
    def _learn_sentiment_words_from_data(self, review_series: pd.Series) -> tuple:
        """Veri setinden yıldız puanlarına göre duygu kelimelerini öğren - ML TABANLI"""
        # Yıldız sütununu bul
        yildiz_col = None
        for col in self.df.columns:
            if 'yildiz' in col.lower() or 'rating' in col.lower() or 'puan' in col.lower():
                yildiz_col = col
                break
        
        if yildiz_col is None:
            # Yıldız sütunu yoksa, veri setinden öğrenilemez
            # Boş liste döndür (fallback yok - tamamen veri setinden öğrenilmeli)
            return ([], [])
        
        # Yorumları yıldız puanlarına göre ayır
        positive_reviews = []
        negative_reviews = []
        
        for idx, review in review_series.items():
            if pd.isna(review):
                continue
            
            # İlgili yıldız puanını al
            if idx < len(self.df):
                yildiz = self.df.loc[idx, yildiz_col]
                if pd.notna(yildiz):
                    try:
                        yildiz_float = float(yildiz)
                        if yildiz_float >= 4.0:  # Pozitif yorum
                            positive_reviews.append(str(review).lower())
                        elif yildiz_float <= 2.0:  # Negatif yorum
                            negative_reviews.append(str(review).lower())
                    except (ValueError, TypeError):
                        pass
        
        # Her iki gruptan da kelimeleri çıkar
        positive_words = self._extract_sentiment_words(positive_reviews, min_freq=2)
        negative_words = self._extract_sentiment_words(negative_reviews, min_freq=2)
        
        # Eğer yeterli kelime yoksa, frekans eşiğini düşür ve tekrar dene
        if len(positive_words) < 5 and len(positive_reviews) > 0:
            positive_words = self._extract_sentiment_words(positive_reviews, min_freq=1)
        if len(negative_words) < 5 and len(negative_reviews) > 0:
            negative_words = self._extract_sentiment_words(negative_reviews, min_freq=1)
        
        # Eğer hala yeterli kelime yoksa, tüm benzersiz kelimeleri al (veri setinden)
        if len(positive_words) < 3 and len(positive_reviews) > 0:
            all_positive_words = []
            for review in positive_reviews:
                words = re.findall(r'\b\w+\b', review.lower())
                all_positive_words.extend([w for w in words if len(w) > 2])
            word_counts = Counter(all_positive_words)
            positive_words = [word for word, count in word_counts.most_common(20)]
        
        if len(negative_words) < 3 and len(negative_reviews) > 0:
            all_negative_words = []
            for review in negative_reviews:
                words = re.findall(r'\b\w+\b', review.lower())
                all_negative_words.extend([w for w in words if len(w) > 2])
            word_counts = Counter(all_negative_words)
            negative_words = [word for word, count in word_counts.most_common(20)]
        
        return (list(set(positive_words)), list(set(negative_words)))
    
    def _extract_sentiment_words(self, reviews: List[str], min_freq: int = 2) -> List[str]:
        """Yorumlardan duygu kelimelerini çıkar"""
        import re
        from collections import Counter
        
        # Türkçe stop words
        stop_words = {'bir', 've', 'ile', 'de', 'da', 'mi', 'mu', 'mü', 'icin', 'var', 'yok', 
                     'olan', 'olanlar', 'gibi', 'kadar', 'daha', 'cok', 'çok', 'bu', 'şu', 'o',
                     'ben', 'sen', 'biz', 'siz', 'onlar', 'burada', 'orada', 'şurada'}
        
        all_words = []
        for review in reviews:
            # Kelimeleri çıkar
            words = re.findall(r'\b[ğüşıöçĞÜŞİÖÇa-zA-Z]+\b', review.lower())
            # Stop words'leri filtrele ve uzun kelimeleri al
            words = [w for w in words if len(w) > 2 and w not in stop_words]
            all_words.extend(words)
        
        # Kelime frekanslarını say
        word_counts = Counter(all_words)
        
        # En sık kullanılan kelimeleri al
        sentiment_words = [word for word, count in word_counts.most_common(100) if count >= min_freq]
        
        return sentiment_words
    
    def _learn_name_description_patterns(self, series: pd.Series) -> Dict[str, Any]:
        """İsim/açıklama pattern'lerini öğren"""
        lengths = series.str.len()
        word_counts = series.str.split().str.len()
        
        return {
            'avg_length': float(lengths.mean()),
            'avg_words': float(word_counts.mean()),
            'length_distribution': {
                'min': int(lengths.min()),
                'max': int(lengths.max()),
                'median': float(lengths.median())
            }
        }
    
    def _learn_general_text_patterns(self, series: pd.Series) -> Dict[str, Any]:
        """Genel metin pattern'lerini öğren"""
        lengths = series.str.len()
        unique_count = series.nunique()
        
        return {
            'unique_count': int(unique_count),
            'avg_length': float(lengths.mean()),
            'diversity_ratio': float(unique_count / len(series))
        }
    
    def _detect_seasonality(self, series: pd.Series) -> Dict[str, Any]:
        """Temporal veride mevsimsellik tespit et"""
        if len(series) < 12:
            return {}
        
        month_counts = series.dt.month.value_counts()
        
        return {
            'peak_months': month_counts.head(3).to_dict(),
            'low_months': month_counts.tail(3).to_dict()
        }
    
    def _find_common_numeric_behaviors(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Sayısal kategorilerde ortak davranışları bul"""
        if not patterns:
            return {}
        
        all_means = [p['distribution']['mean'] for p in patterns.values() if 'distribution' in p]
        all_stds = [p['distribution']['std'] for p in patterns.values() if 'distribution' in p]
        
        return {
            'mean_range': {'min': float(min(all_means)), 'max': float(max(all_means))} if all_means else {},
            'std_range': {'min': float(min(all_stds)), 'max': float(max(all_stds))} if all_stds else {}
        }
    
    def _find_common_text_behaviors(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Metin kategorilerde ortak davranışları bul"""
        if not patterns:
            return {}
        
        return {
            'pattern_count': len(patterns),
            'common_attributes': list(patterns.keys())
        }
    
    def get_learned_patterns_summary(self) -> Dict[str, Any]:
        """Öğrenilen pattern'lerin özetini getir"""
        summary = {
            'total_categories': len(self.learned_patterns),
            'categories': {}
        }
        
        for category, patterns in self.learned_patterns.items():
            summary['categories'][category] = {
                'type': patterns.get('category_type'),
                'attribute_count': len(patterns.get('patterns', {})),
                'has_common_behaviors': 'common_behaviors' in patterns
            }
        
        return summary

