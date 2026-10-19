from .data_processor import DataProcessor
from .llm_engine import LLMEngine
from .llm_input_generator import LLMInputGenerator
from .model_selector import ModelSelector
from typing import Dict, List, Optional

class RecommendationEngine:
    def __init__(self, urunler_path: str, yorumlar_path: str, model: str = "llama-3.3-70b-versatile", provider: str = "groq"):
        self.data_processor = DataProcessor(urunler_path, yorumlar_path)
        self.llm_engine = LLMEngine(model=model, provider=provider)
        
        # Yeni mimari bileşenleri
        self.input_generator = None
        self.model_selector = None
        
        self.initialized = False
        
    def initialize(self):
        """Sistemi başlat - YENİ MİMARİ İLE"""
        if not self.initialized:
            print("\n" + "=" * 60)
            print("SİSTEM BAŞLATILIYOR - YENİ MİMARİ")
            print("=" * 60)
            
            # 1. Veri yükleme
            self.data_processor.load_data()
            
            # 2. Öznitelik analizi (tokenizasyon, kategorileştirme, öğrenme)
            self.data_processor.analyze_attributes()
            
            # 3. Tokenize edilmiş verileri al
            tokenized_data = self.data_processor.get_tokenized_data()
            
            # 4. LLM girdi üreticiyi başlat (SmartQueryParser ile)
            self.input_generator = LLMInputGenerator(
                tokenized_attributes={
                    **tokenized_data['urunler']['tokenized'],
                    **tokenized_data['yorumlar']['tokenized']
                },
                semantic_meanings={
                    **tokenized_data['urunler']['semantic'],
                    **tokenized_data['yorumlar']['semantic']
                },
                learned_patterns={
                    **tokenized_data['urunler']['learned_patterns'],
                    **tokenized_data['yorumlar']['learned_patterns']
                },
                categories={
                    **tokenized_data['urunler']['categories'],
                    **tokenized_data['yorumlar']['categories']
                },
                smart_parser=self.data_processor.smart_parser  # SmartQueryParser'ı geçir
            )
            
            self.initialized = True
            print("\n" + "=" * 60)
            print("✓ SİSTEM BAŞARIYLA BAŞLATILDI")
            print("=" * 60 + "\n")
    
    def get_recommendation(self, user_query: str, product_limit: int = 10, review_limit: int = 1) -> Dict:
        """Kullanıcı sorgusuna göre kombin öner - YENİ MİMARİ İLE"""
        if not self.initialized:
            self.initialize()
        
        print("\n" + "=" * 60)
        print("ÖNERİ İŞLEMİ BAŞLATILIYOR")
        print("=" * 60)
        
        # ADIM 1: Ürünleri ve yorumları al
        print("\n1️⃣ Ürünler ve yorumlar yükleniyor...")
        products = self.data_processor.get_product_context(user_query=user_query, limit=product_limit)
        reviews = self.data_processor.get_reviews_context(limit=review_limit)
        print(f"   ✓ {len(products)} ürün, {len(reviews)} yorum yüklendi")
        
        # ADIM 2: Çıktı gereksinimlerine göre LLM girdisi üret
        print("\n2️⃣ Çıktı gereksinimlerine göre LLM girdisi üretiliyor...")
        tokenized_data = self.data_processor.get_tokenized_data()
        
        # Model seçici için output requirements oluştur
        output_requirements = self.input_generator._infer_output_requirements(user_query)
        
        # Model seçiciyi başlat
        self.model_selector = ModelSelector(
            output_requirements=output_requirements,
            learned_patterns={
                **tokenized_data['urunler']['learned_patterns'],
                **tokenized_data['yorumlar']['learned_patterns']
            },
            semantic_meanings={
                **tokenized_data['urunler']['semantic'],
                **tokenized_data['yorumlar']['semantic']
            }
        )
        
        # LLM girdisi üret
        llm_input = self.input_generator.generate_input_for_output(
            user_query=user_query,
            products=products,
            reviews=reviews,
            output_requirements=output_requirements
        )
        print("   ✓ LLM girdisi üretildi")
        
        # ADIM 3: LLM'den çıktı al
        print("\n3️⃣ LLM'den çıktı alınıyor...")
        llm_response = self.llm_engine.get_recommendation(llm_input)
        print("   ✓ LLM çıktısı alındı")
        
        # ADIM 4: Model çıktısından uygun parçaları seç
        print("\n4️⃣ Model çıktısından uygun parçalar seçiliyor...")
        selected_output = self.model_selector.select_output(llm_response)
        print(f"   ✓ {len(selected_output.get('kombinasyon', []))} ürün seçildi")
        
        # ADIM 5: Seçilen parçaları Grok/Llama ile yorumla (TOKEN TASARRUFU İÇİN ATLANIYOR)
        # Output interpreter her ürün için ayrı LLM çağrısı yapıyor, bu çok fazla token kullanıyor
        # Bu yüzden yorumlama adımını atlıyoruz - LLM zaten yeterince iyi açıklamalar üretiyor
        print("\n5️⃣ Yorumlama adımı atlanıyor (token tasarrufu için)...")
        interpreted_output = selected_output  # Yorumlama yapmadan direkt kullan
        print("   ✓ Çıktı hazır")
        
        print("\n" + "=" * 60)
        print("✓ ÖNERİ İŞLEMİ TAMAMLANDI")
        print("=" * 60 + "\n")
        
        return interpreted_output



