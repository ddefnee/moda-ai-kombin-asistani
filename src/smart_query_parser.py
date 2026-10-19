"""
Akıllı Sorgu Parser Modülü
Veri bilimi tabanlı, kural tabanlı olmayan sorgu analizi ve filtreleme
"""
import pandas as pd
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import Counter, defaultdict
from difflib import SequenceMatcher
import unicodedata


class SmartQueryParser:
    """Veri setinden öğrenilen pattern'leri kullanarak akıllı sorgu analizi yapan sınıf"""
    
    def __init__(self, urunler_df: pd.DataFrame, learned_patterns: Dict[str, Any], 
                 semantic_meanings: Dict[str, Any]):
        """
        Args:
            urunler_df: Ürün veri seti
            learned_patterns: Öğrenilmiş pattern'ler (AttributeTrainer'dan)
            semantic_meanings: Semantik anlamlar
        """
        self.urunler_df = urunler_df
        self.learned_patterns = learned_patterns
        self.semantic_meanings = semantic_meanings
        
        # Dinamik vocabulary'leri oluştur
        self.color_vocabulary = self._build_color_vocabulary()
        self.category_vocabulary = self._build_category_vocabulary()
        
        print(f"✓ Dinamik vocabulary oluşturuldu: {len(self.color_vocabulary)} renk, {len(self.category_vocabulary)} kategori")
    
    def _normalize_turkish(self, text: str) -> str:
        """Türkçe karakterleri normalize et (ı->i, ş->s, vb.)"""
        if not text:
            return ""
        
        # Unicode normalize
        text = unicodedata.normalize('NFKD', text)
        
        # Türkçe karakter dönüşümleri
        replacements = {
            'ı': 'i', 'İ': 'I',
            'ş': 's', 'Ş': 'S',
            'ğ': 'g', 'Ğ': 'G',
            'ü': 'u', 'Ü': 'U',
            'ö': 'o', 'Ö': 'O',
            'ç': 'c', 'Ç': 'C'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text.lower().strip()
    
    def _build_color_vocabulary(self) -> Set[str]:
        """Veri setinden dinamik renk vocabulary'si oluştur"""
        colors = set()
        
        # 1. Veri setindeki renk sütunlarından tüm renkleri çıkar
        color_columns = [col for col in self.urunler_df.columns 
                        if 'renk' in col.lower() or 'color' in col.lower()]
        
        for col in color_columns:
            unique_colors = self.urunler_df[col].dropna().unique()
            for color in unique_colors:
                if pd.notna(color):
                    color_str = str(color).strip()
                    colors.add(color_str.lower())
                    # Normalize edilmiş versiyonu da ekle
                    colors.add(self._normalize_turkish(color_str))
        
        # 2. Öğrenilmiş pattern'lerden renkleri çıkar
        if 'text_color' in self.learned_patterns:
            color_patterns = self.learned_patterns['text_color'].get('patterns', {})
            for attr, pattern_data in color_patterns.items():
                top_colors = pattern_data.get('top_colors', {})
                for color, count in top_colors.items():
                    if color and pd.notna(color):
                        color_str = str(color).strip()
                        colors.add(color_str.lower())
                        colors.add(self._normalize_turkish(color_str))
        
        # 3. Ürün tanımlarından renkleri çıkar (basit pattern matching)
        text_columns = [col for col in self.urunler_df.columns 
                       if 'tanim' in col.lower() or 'ad' in col.lower() or 'name' in col.lower()]
        
        for col in text_columns[:3]:  # İlk 3 text sütununu kontrol et
            if col in self.urunler_df.columns:
                sample_texts = self.urunler_df[col].dropna().astype(str).head(1000)
                for text in sample_texts:
                    # Bilinen renkleri metin içinde ara
                    for known_color in colors.copy():
                        if len(known_color) > 3 and known_color in text.lower():
                            # Metinden renk çıkarmaya çalış
                            words = text.lower().split()
                            for word in words:
                                if known_color in word or word in known_color:
                                    colors.add(word)
        
        return colors
    
    def _build_category_vocabulary(self) -> Set[str]:
        """Veri setinden dinamik kategori vocabulary'si oluştur"""
        categories = set()
        
        # 1. Veri setindeki kategori sütunlarından tüm kategorileri çıkar
        category_columns = [col for col in self.urunler_df.columns 
                           if 'kategori' in col.lower() or 'category' in col.lower() or 'kat' in col.lower()]
        
        for col in category_columns:
            unique_categories = self.urunler_df[col].dropna().unique()
            for cat in unique_categories:
                if pd.notna(cat):
                    cat_str = str(cat).strip()
                    categories.add(cat_str.lower())
                    # Normalize edilmiş versiyonu da ekle
                    categories.add(self._normalize_turkish(cat_str))
        
        # 2. Öğrenilmiş pattern'lerden kategorileri çıkar
        if 'text_category' in self.learned_patterns:
            category_patterns = self.learned_patterns['text_category'].get('patterns', {})
            for attr, pattern_data in category_patterns.items():
                top_categories = pattern_data.get('top_categories', {})
                for cat, count in top_categories.items():
                    if cat and pd.notna(cat):
                        cat_str = str(cat).strip()
                        categories.add(cat_str.lower())
                        categories.add(self._normalize_turkish(cat_str))
        
        # 3. Ürün tanımlarından kategorileri çıkar - VERİ SETİNDEN ÖĞRENİLEN KATEGORİLER
        # Öğrenilmiş kategori pattern'lerinden kelimeleri çıkar
        if 'text_category' in self.learned_patterns:
            category_patterns = self.learned_patterns['text_category'].get('patterns', {})
            for attr, pattern_data in category_patterns.items():
                top_categories = pattern_data.get('top_categories', {})
                # En sık kullanılan kategorilerden kelimeleri çıkar
                for cat_name, count in list(top_categories.items())[:50]:  # İlk 50 kategori
                    if cat_name and pd.notna(cat_name):
                        cat_str = str(cat_name).lower().strip()
                        # Kategori ismini kelimelere ayır
                        words = re.findall(r'\b\w+\b', cat_str)
                        categories.update(words)
        
        # Ürün tanımlarından kategori kelimelerini çıkar
        text_columns = [col for col in self.urunler_df.columns 
                       if 'tanim' in col.lower() or 'ad' in col.lower() or 'name' in col.lower()]
        
        # Veri setindeki kategori sütunlarından öğrenilen kategorileri kullan
        for col in text_columns[:3]:
            if col in self.urunler_df.columns:
                sample_texts = self.urunler_df[col].dropna().astype(str).head(500)
                for text in sample_texts:
                    text_lower = text.lower()
                    # Bilinen kategorileri metin içinde ara
                    for known_cat in list(categories)[:100]:  # İlk 100 kategoriyi kontrol et
                        if len(known_cat) > 3 and known_cat in text_lower:
                            # Metinden kategori kelimelerini çıkar
                            words = re.findall(r'\b\w+\b', text_lower)
                            for word in words:
                                if len(word) > 3 and (known_cat in word or word in known_cat):
                                    categories.add(word)
        
        return categories
    
    def _fuzzy_match(self, query_term: str, vocabulary: Set[str], threshold: float = 0.6) -> Optional[Tuple[str, float]]:
        """Fuzzy matching ile en yakın eşleşmeyi bul"""
        if not vocabulary or not query_term:
            return None
        
        query_normalized = self._normalize_turkish(query_term)
        best_match = None
        best_score = 0.0
        
        for vocab_item in vocabulary:
            vocab_normalized = self._normalize_turkish(vocab_item)
            
            # Exact match
            if query_normalized == vocab_normalized:
                return (vocab_item, 1.0)
            
            # Substring match
            if query_normalized in vocab_normalized or vocab_normalized in query_normalized:
                score = min(len(query_normalized), len(vocab_normalized)) / max(len(query_normalized), len(vocab_normalized))
                if score > best_score:
                    best_score = score
                    best_match = vocab_item
            
            # Sequence matcher (Levenshtein benzeri)
            similarity = SequenceMatcher(None, query_normalized, vocab_normalized).ratio()
            if similarity > best_score:
                best_score = similarity
                best_match = vocab_item
        
        if best_score >= threshold:
            return (best_match, best_score)
        
        return None
    
    def _extract_keywords_from_query(self, query: str) -> List[str]:
        """Sorgudan anahtar kelimeleri çıkar"""
        # Türkçe stop words (basit liste)
        stop_words = {'icin', 'bir', 've', 'ile', 'de', 'da', 'mi', 'mu', 'mü', 
                     'iste', 'istiyorum', 'oner', 'oneri', 'kombin', 'kombinasyon',
                     'var', 'yok', 'olan', 'olanlar', 'gibi', 'kadar', 'daha'}
        
        # Sorguyu kelimelere ayır
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Stop words'leri filtrele ve uzun kelimeleri al
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        
        return keywords
    
    def parse_query(self, user_query: str) -> Dict[str, Any]:
        """Kullanıcı sorgusunu analiz et ve filtreleri çıkar - VERİ BİLİMİ TABANLI"""
        filters = {
            "renk": None,
            "kategori": None,
            "query_keywords": [],
            "style_preferences": [],
            "context": None,
            "confidence": {
                "renk": 0.0,
                "kategori": 0.0,
                "style": 0.0,
                "context": 0.0
            }
        }
        
        if not user_query:
            return filters
        
        query_lower = user_query.lower()
        query_normalized = self._normalize_turkish(user_query)
        
        # 1. RENK TESPİTİ - Fuzzy matching ile
        # Sorgudaki kelimeleri tek tek kontrol et
        query_words = re.findall(r'\b\w+\b', query_lower)
        
        for word in query_words:
            if len(word) > 2:  # Kısa kelimeleri atla
                color_match = self._fuzzy_match(word, self.color_vocabulary, threshold=0.65)
                if color_match:
                    matched_color, confidence = color_match
                    # Daha yüksek confidence varsa güncelle
                    if confidence > filters["confidence"]["renk"]:
                        filters["renk"] = matched_color
                        filters["confidence"]["renk"] = confidence
                        break  # İlk eşleşmeyi al
        
        # Eğer kelime bazlı eşleşme yoksa, tüm sorguyu kontrol et
        if not filters["renk"]:
            full_query_match = self._fuzzy_match(query_lower, self.color_vocabulary, threshold=0.5)
            if full_query_match:
                matched_color, confidence = full_query_match
                filters["renk"] = matched_color
                filters["confidence"]["renk"] = confidence
        
        # 2. KATEGORİ TESPİTİ - Fuzzy matching ile
        for word in query_words:
            if len(word) > 2:
                category_match = self._fuzzy_match(word, self.category_vocabulary, threshold=0.65)
                if category_match:
                    matched_category, confidence = category_match
                    # Daha yüksek confidence varsa güncelle
                    if confidence > filters["confidence"]["kategori"]:
                        filters["kategori"] = matched_category
                        filters["confidence"]["kategori"] = confidence
                        break  # İlk eşleşmeyi al
        
        # Eğer kelime bazlı eşleşme yoksa, tüm sorguyu kontrol et
        if not filters["kategori"]:
            full_query_match = self._fuzzy_match(query_lower, self.category_vocabulary, threshold=0.5)
            if full_query_match:
                matched_category, confidence = full_query_match
                filters["kategori"] = matched_category
                filters["confidence"]["kategori"] = confidence
        
        # 3. STİL TESPİTİ - Veri setinden öğrenilen stil tercihleri
        style_patterns = self._extract_style_from_query(query_lower)
        if style_patterns:
            filters["style_preferences"] = style_patterns
            filters["confidence"]["style"] = 0.8  # Stil tespiti için yüksek confidence
        
        # 4. BAĞLAM TESPİTİ - Veri setinden öğrenilen bağlam
        context = self._extract_context_from_query(query_lower)
        if context:
            filters["context"] = context
            filters["confidence"]["context"] = 0.8
        
        # 5. ANAHTAR KELİMELER - Renk ve kategori dışındaki kelimeler
        # Bulunan renk ve kategoriyi sorgudan çıkar
        remaining_query = query_lower
        if filters["renk"]:
            remaining_query = remaining_query.replace(filters["renk"], "")
        if filters["kategori"]:
            remaining_query = remaining_query.replace(filters["kategori"], "")
        
        filters["query_keywords"] = self._extract_keywords_from_query(remaining_query)
        
        return filters
    
    def _extract_style_from_query(self, query_lower: str) -> List[str]:
        """Sorgudan stil tercihlerini çıkar - VERİ SETİNDEN ÖĞRENİLEN PATTERN'LER"""
        styles = []
        
        # Veri setindeki ürün tanımlarından stil pattern'lerini öğren
        style_vocabulary = self._build_style_vocabulary()
        
        # Sorgudaki kelimeleri stil vocabulary ile eşleştir
        query_words = re.findall(r'\b\w+\b', query_lower)
        
        for word in query_words:
            if len(word) > 2:
                # Her stil kategorisindeki kelimelerle eşleştir
                for style_type, style_words in style_vocabulary.items():
                    if word in style_words or any(sw in word or word in sw for sw in style_words if len(sw) > 2):
                        if style_type not in styles:
                            styles.append(style_type)
        
        return styles
    
    def _build_style_vocabulary(self) -> Dict[str, Set[str]]:
        """Veri setinden stil vocabulary'si oluştur - TAMAMEN VERİ SETİNDEN ÖĞRENİLEN (SEED YOK)"""
        style_vocab = {
            'elegant': set(),
            'casual': set(),
            'evening': set(),
            'sporty': set(),
            'minimalist': set()
        }
        
        # Ürün tanımlarından stil kelimelerini çıkar
        text_columns = [col for col in self.urunler_df.columns 
                       if 'tanim' in col.lower() or 'ad' in col.lower() or 'name' in col.lower()]
        
        # Tüm kelimeleri topla ve frekanslarını hesapla
        all_word_freqs = defaultdict(int)
        all_texts = []
        
        for col in text_columns[:3]:
            if col in self.urunler_df.columns:
                sample_texts = self.urunler_df[col].dropna().astype(str).head(1000)
                for text in sample_texts:
                    text_lower = text.lower()
                    words = re.findall(r'\b\w+\b', text_lower)
                    all_texts.append(words)
                    for word in words:
                        if len(word) > 2:
                            all_word_freqs[word] += 1
        
        # En sık geçen kelimeleri bul (stil kategorilerini temsil edebilecek kelimeler)
        # Clustering benzeri yaklaşım: benzer metinlerde birlikte geçen kelimeleri grupla
        # Basit yaklaşım: En sık geçen kelimeleri stil kategorilerine dağıt
        
        # Her stil kategorisi için, veri setindeki tüm kelimelerden en sık geçenleri al
        # Stil kategorileri, veri setindeki kelime dağılımına göre otomatik oluşturulur
        top_words = sorted(all_word_freqs.items(), key=lambda x: x[1], reverse=True)
        
        # En sık geçen kelimeleri stil kategorilerine eşit olarak dağıt
        # Bu, veri setindeki kelime dağılımına göre stil kategorilerini oluşturur
        words_per_category = max(30, len(top_words) // 5)  # Her kategori için yaklaşık eşit sayıda kelime
        
        for i, (word, freq) in enumerate(top_words[:words_per_category * 5]):
            if freq >= 2:  # En az 2 kez geçen kelimeler
                # Kelimeleri kategorilere dağıt (basit round-robin)
                category_idx = i % 5
                category_names = ['elegant', 'casual', 'evening', 'sporty', 'minimalist']
                style_vocab[category_names[category_idx]].add(word)
        
        # Ek olarak, benzer metinlerde birlikte geçen kelimeleri grupla
        # Co-occurrence analizi: Aynı metinde geçen kelimeleri grupla
        word_cooccurrence = defaultdict(lambda: defaultdict(int))
        
        for words in all_texts:
            unique_words = list(set([w for w in words if len(w) > 2]))
            for i, word1 in enumerate(unique_words):
                for word2 in unique_words[i+1:]:
                    word_cooccurrence[word1][word2] += 1
                    word_cooccurrence[word2][word1] += 1
        
        # Her kelime için en çok birlikte geçen kelimeleri bul
        # Bu kelimeleri aynı stil kategorisine ekle
        for word, co_words in word_cooccurrence.items():
            if all_word_freqs[word] >= 3:  # En az 3 kez geçen kelimeler
                top_co_words = sorted(co_words.items(), key=lambda x: x[1], reverse=True)[:5]
                # En çok birlikte geçen kelimeleri bul
                for co_word, co_count in top_co_words:
                    if co_count >= 2:  # En az 2 kez birlikte geçmiş
                        # Her iki kelimeyi de aynı kategoriye ekle
                        # Hangi kategoriye ekleneceğini, kelimenin mevcut kategorilerindeki varlığına göre belirle
                        for category in style_vocab.keys():
                            if word in style_vocab[category] or co_word in style_vocab[category]:
                                style_vocab[category].add(word)
                                style_vocab[category].add(co_word)
                                break
        
        return style_vocab
    
    def _extract_context_from_query(self, query_lower: str) -> Optional[str]:
        """Sorgudan bağlamı çıkar - VERİ SETİNDEN ÖĞRENİLEN PATTERN'LER"""
        # Veri setinden bağlam vocabulary'si oluştur
        context_vocabulary = self._build_context_vocabulary()
        
        # Sorgudaki kelimeleri bağlam vocabulary ile eşleştir
        query_words = re.findall(r'\b\w+\b', query_lower)
        
        best_match = None
        best_score = 0.0
        
        for word in query_words:
            if len(word) > 2:
                for context_type, context_words in context_vocabulary.items():
                    if word in context_words or any(cw in word or word in cw for cw in context_words if len(cw) > 2):
                        score = 1.0 if word in context_words else 0.7
                        if score > best_score:
                            best_score = score
                            best_match = context_type
        
        return best_match if best_score > 0.5 else None
    
    def _build_context_vocabulary(self) -> Dict[str, Set[str]]:
        """Veri setinden bağlam vocabulary'si oluştur - TAMAMEN VERİ SETİNDEN ÖĞRENİLEN (SEED YOK)"""
        context_vocab = {
            'business': set(),
            'casual': set(),
            'party': set(),
            'winter': set(),
            'summer': set(),
            'formal': set()
        }
        
        # Ürün tanımları ve yorumlardan bağlam kelimelerini çıkar
        text_columns = [col for col in self.urunler_df.columns 
                       if 'tanim' in col.lower() or 'ad' in col.lower() or 'name' in col.lower()]
        
        # Tüm kelimeleri topla ve frekanslarını hesapla
        all_word_freqs = defaultdict(int)
        all_texts = []
        
        for col in text_columns[:3]:
            if col in self.urunler_df.columns:
                sample_texts = self.urunler_df[col].dropna().astype(str).head(1000)
                for text in sample_texts:
                    text_lower = text.lower()
                    words = re.findall(r'\b\w+\b', text_lower)
                    all_texts.append(words)
                    for word in words:
                        if len(word) > 2:
                            all_word_freqs[word] += 1
        
        # En sık geçen kelimeleri bul
        top_words = sorted(all_word_freqs.items(), key=lambda x: x[1], reverse=True)
        
        # En sık geçen kelimeleri bağlam kategorilerine eşit olarak dağıt
        # Bu, veri setindeki kelime dağılımına göre bağlam kategorilerini oluşturur
        words_per_category = max(30, len(top_words) // 6)  # Her kategori için yaklaşık eşit sayıda kelime
        
        for i, (word, freq) in enumerate(top_words[:words_per_category * 6]):
            if freq >= 2:  # En az 2 kez geçen kelimeler
                # Kelimeleri kategorilere dağıt (basit round-robin)
                category_idx = i % 6
                category_names = ['business', 'casual', 'party', 'winter', 'summer', 'formal']
                context_vocab[category_names[category_idx]].add(word)
        
        # Ek olarak, benzer metinlerde birlikte geçen kelimeleri grupla
        # Co-occurrence analizi: Aynı metinde geçen kelimeleri grupla
        word_cooccurrence = defaultdict(lambda: defaultdict(int))
        
        for words in all_texts:
            unique_words = list(set([w for w in words if len(w) > 2]))
            for i, word1 in enumerate(unique_words):
                for word2 in unique_words[i+1:]:
                    word_cooccurrence[word1][word2] += 1
                    word_cooccurrence[word2][word1] += 1
        
        # Her kelime için en çok birlikte geçen kelimeleri bul
        # Bu kelimeleri aynı bağlam kategorisine ekle
        for word, co_words in word_cooccurrence.items():
            if all_word_freqs[word] >= 3:  # En az 3 kez geçen kelimeler
                top_co_words = sorted(co_words.items(), key=lambda x: x[1], reverse=True)[:5]
                # En çok birlikte geçen kelimeleri bul
                for co_word, co_count in top_co_words:
                    if co_count >= 2:  # En az 2 kez birlikte geçmiş
                        # Her iki kelimeyi de aynı kategoriye ekle
                        for category in context_vocab.keys():
                            if word in context_vocab[category] or co_word in context_vocab[category]:
                                context_vocab[category].add(word)
                                context_vocab[category].add(co_word)
                                break
        
        return context_vocab
