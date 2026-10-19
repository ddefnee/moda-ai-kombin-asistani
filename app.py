import streamlit as st
from src.recommendation_engine import RecommendationEngine
import json
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Sayfa ayarları
st.set_page_config(
    page_title="Moda AI - Kombin Önerisi",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Profesyonel ve zarif tasarım - Soft pastel tonlar
st.markdown("""
    <style>
    /* Ana arka plan - Soft lavanta/mor gradient */
    .stApp {
        background: linear-gradient(180deg, #F5F0FF 0%, #E8E0F0 50%, #F0E8F8 100%) !important;
    }
    
    .main .block-container {
        background: transparent !important;
        padding-top: 2rem;
    }
    
    /* Üst header bar - Soft mor gradient */
    header[data-testid="stHeader"] {
        background: linear-gradient(90deg, #D8BFD8 0%, #E6D9F2 100%) !important;
        border-bottom: 1px solid rgba(200, 162, 200, 0.3) !important;
        box-shadow: 0 2px 8px rgba(200, 162, 200, 0.1) !important;
    }
    
    header[data-testid="stHeader"] * {
        color: #5A4A5A !important;
    }
    
    /* Üst bar'daki butonlar ve yazılar */
    .stApp > header,
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] div,
    header[data-testid="stHeader"] span {
        background: transparent !important;
        color: #FFFFFF !important;
    }
    
    /* Genel yazı renkleri - Koyu gri (okunabilirlik için) */
    .stMarkdown, .stText, p, div, span, label {
        color: #4A4A4A !important;
    }
    
    /* Sidebar yazıları - Koyu bej */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label {
        color: #5A4A4A !important;
    }
    
    /* Ürün açıklamaları ve detaylar - Koyu gri */
    .stExpander label,
    .stExpander p,
    .stExpander div,
    .stExpander strong,
    .stExpander span {
        color: #4A4A4A !important;
    }
    
    /* Chat mesajları - Koyu gri */
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] div,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] {
        color: #4A4A4A !important;
    }
    
    /* Kullanıcı girdisi ve AI cevabı - Koyu gri */
    [data-testid="stChatInput"] textarea {
        color: #4A4A4A !important;
        background: rgba(255, 255, 255, 0.8) !important;
    }
    
    [data-testid="stChatInput"] textarea::placeholder {
        color: #9A9A9A !important;
    }
    
    /* Chat input container */
    [data-testid="stChatInputContainer"] {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(10px);
    }
    
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #C8A2C8 0%, #D8BFD8 50%, #E6D9F2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin: 0;
        padding: 0.5rem 0 0.5rem 0.5rem;
        letter-spacing: -0.5px;
    }
    
    /* Column gap'i azaltmak için */
    [data-testid="column"] {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    .sub-header {
        text-align: center;
        color: #7A6A7A;
        margin-bottom: 2rem;
        font-size: 1.1rem;
        font-weight: 400;
        letter-spacing: 0.3px;
    }
    /* Hızlı öneriler butonları - Soft gradient (sidebar'da) - Küçültülmüş */
    [data-testid="stSidebar"] .stButton>button {
        background: linear-gradient(135deg, #F4E6F4 0%, #E8D9E8 100%) !important;
        border: 1.5px solid #D8BFD8 !important;
        border-radius: 10px;
        padding: 0.5rem 0.8rem;
        margin: 0.3rem 0;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        color: #6A5A6A !important;
        font-weight: 500;
        font-size: 0.85rem;
        box-shadow: 0 2px 4px rgba(200, 162, 200, 0.1);
        line-height: 1.3;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background: linear-gradient(135deg, #E8D9E8 0%, #E0D0E0 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(200, 162, 200, 0.2);
        border-color: #C8A2C8 !important;
        color: #5A4A5A !important;
    }
    
    /* Sidebar butonları içindeki yazılar */
    [data-testid="stSidebar"] button {
        color: #6A5A6A !important;
    }
    .stExpander {
        border: 1.5px solid #E0D0E0;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        box-shadow: 0 2px 8px rgba(200, 162, 200, 0.1);
        margin: 1rem 0;
    }
    .stExpander label {
        color: #5A4A5A !important;
        font-weight: 600;
    }
    .product-card {
        background: linear-gradient(135deg, #FAF5FF 0%, #F5F0FF 100%);
        border: 1.5px solid #E0D0E0;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(200, 162, 200, 0.15);
    }
    .stButton>button {
        background: linear-gradient(135deg, #D8BFD8 0%, #C8A2C8 100%);
        color: #FFFFFF !important;
        border: none;
        border-radius: 20px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        box-shadow: 0 2px 6px rgba(200, 162, 200, 0.2);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #C8A2C8 0%, #B892B8 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(200, 162, 200, 0.3);
        color: #FFFFFF !important;
    }
    /* Sidebar - Soft bej/krem gradient */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FAF5F0 0%, #FFF8F0 100%) !important;
        border-right: 1px solid rgba(200, 162, 200, 0.2);
    }
    
    /* Sidebar içindeki yazılar - Koyu bej */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: #5A4A4A !important;
    }
    
    /* Başlıklar - Koyu mor/gri */
    h1, h2, h3, h4, h5, h6 {
        color: #5A4A5A !important;
    }
    
    /* Strong ve bold yazılar - Koyu mor */
    strong, b {
        color: #6A5A6A !important;
    }
    
    /* Info mesajları (Açıklama) - Soft lavanta arka plan */
    .stInfo {
        background: linear-gradient(135deg, #F5F0FF 0%, #F0E8F8 100%) !important;
        border-left: 4px solid #C8A2C8 !important;
        color: #5A4A5A !important;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(200, 162, 200, 0.1);
    }
    
    .stInfo p,
    .stInfo div,
    .stInfo span {
        color: #5A4A5A !important;
    }
    
    /* Success mesajları (Stil Notları) - Soft pembe arka plan */
    .stSuccess {
        background: linear-gradient(135deg, #FFF0F5 0%, #FFE8F0 100%) !important;
        border-left: 4px solid #F4C2C2 !important;
        color: #6A5A6A !important;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(244, 194, 194, 0.15);
    }
    
    .stSuccess p,
    .stSuccess div,
    .stSuccess span {
        color: #6A5A6A !important;
    }
    
    /* Chat input container - Soft lavanta gradient */
    [data-testid="stChatInputContainer"],
    [data-testid="stChatInputContainer"] > div,
    [data-testid="stChatInputContainer"] > div > div,
    [data-testid="stChatInputContainer"] > div > div > div,
    [data-testid="stChatInputContainer"] *,
    div[data-testid="stChatInputContainer"],
    section[data-testid="stChatInputContainer"],
    .stApp [data-testid="stChatInputContainer"],
    .stApp [data-testid="stChatInputContainer"] > *,
    .stApp [data-testid="stChatInputContainer"] > * > *,
    .stApp [data-testid="stChatInputContainer"] > * > * > *,
    /* Parent elementleri de override et */
    .stApp > div:has([data-testid="stChatInputContainer"]),
    .stApp > div:has([data-testid="stChatInputContainer"]) > div,
    .stApp > div:has([data-testid="stChatInputContainer"]) > div > div,
    .stApp > div:has([data-testid="stChatInputContainer"]) > div > div > div {
        background: linear-gradient(180deg, #F5F0FF 0%, #F0E8F8 100%) !important;
        background-color: #F5F0FF !important;
        border: none !important;
    }
    
    /* Inline style'ları override etmek için - tüm olası kombinasyonlar */
    [data-testid="stChatInputContainer"][style],
    [data-testid="stChatInputContainer"][style*="background"],
    [data-testid="stChatInputContainer"] > div[style],
    [data-testid="stChatInputContainer"] > div[style*="background"],
    [data-testid="stChatInputContainer"] > div > div[style],
    [data-testid="stChatInputContainer"] > div > div[style*="background"],
    .stApp > div:has([data-testid="stChatInputContainer"])[style],
    .stApp > div:has([data-testid="stChatInputContainer"])[style*="background"] {
        background: linear-gradient(180deg, #F5F0FF 0%, #F0E8F8 100%) !important;
        background-color: #F5F0FF !important;
    }
    
    /* Chat input textarea */
    [data-testid="stChatInput"] textarea {
        background: rgba(255, 255, 255, 0.9) !important;
        color: #4A4A4A !important;
        border: 1.5px solid #E0D0E0 !important;
        border-radius: 16px !important;
        padding: 0.8rem 1rem !important;
        box-shadow: 0 2px 8px rgba(200, 162, 200, 0.1) !important;
    }
    
    [data-testid="stChatInput"] textarea::placeholder {
        color: #9A9A9A !important;
    }
    
    [data-testid="stChatInput"] textarea:focus {
        background: rgba(255, 255, 255, 1) !important;
        border: 1.5px solid #C8A2C8 !important;
        outline: none !important;
        box-shadow: 0 4px 12px rgba(200, 162, 200, 0.2) !important;
    }
    
    /* Footer ve alt kısım - Soft lavanta */
    footer,
    footer *,
    [data-testid="stFooter"],
    [data-testid="stFooter"] * {
        background: linear-gradient(180deg, #F5F0FF 0%, #F0E8F8 100%) !important;
        color: #6A5A6A !important;
    }
    
    /* Alt kısım genel arka plan - tüm olası selector'lar */
    .stApp > footer,
    .stApp > footer *,
    .element-container:has([data-testid="stChatInputContainer"]),
    .element-container:has([data-testid="stChatInputContainer"]) *,
    .stApp > div:last-child,
    .stApp > div:last-child > div,
    .stApp > div:last-child > div > div,
    div[data-testid="stChatInputContainer"],
    section[data-testid="stChatInputContainer"] {
        background: linear-gradient(180deg, #F5F0FF 0%, #F0E8F8 100%) !important;
    }
    
    /* Streamlit'in bottom bar'ını override et */
    .stApp > header ~ div:last-of-type,
    .stApp > div[data-testid="stBottom"],
    .stApp > div[data-testid="stBottom"] > div,
    .stApp > div[data-testid="stBottom"] > div > div {
        background: linear-gradient(180deg, #F5F0FF 0%, #F0E8F8 100%) !important;
    }
    
    /* Tüm siyah arka planları override et - chat input alanı için */
    div[style*="background"][style*="black"],
    div[style*="background"][style*="#000"],
    div[style*="background-color: rgb(0, 0, 0)"],
    div[style*="background-color: #000000"],
    div[style*="background-color: rgb(14, 17, 23)"],
    div[style*="background-color: #0E1117"],
    .stApp > div:has([data-testid="stChatInputContainer"]),
    .stApp > div:has([data-testid="stChatInputContainer"]) > div,
    .stApp > div:has([data-testid="stChatInputContainer"]) > div > div {
        background: linear-gradient(180deg, #F5F0FF 0%, #F0E8F8 100%) !important;
        background-color: #F5F0FF !important;
    }
    
    /* Streamlit'in varsayılan dark theme arka planlarını override et */
    .stApp > div:last-child:not([data-testid="stSidebar"]),
    .stApp > div:last-child:not([data-testid="stSidebar"]) > div,
    .stApp > div:last-child:not([data-testid="stSidebar"]) > div > div,
    /* Tüm olası chat input wrapper'ları */
    .stApp > div:has(> [data-testid="stChatInputContainer"]),
    .stApp > div:has(> div > [data-testid="stChatInputContainer"]),
    .stApp > div:has(> div > div > [data-testid="stChatInputContainer"]),
    /* Genel dark background override */
    div[class*="stChat"],
    div[class*="chat"],
    section[class*="stChat"],
    section[class*="chat"] {
        background: linear-gradient(180deg, #F5F0FF 0%, #F0E8F8 100%) !important;
        background-color: #F5F0FF !important;
    }

    /* Ekstra güçlü override - yeni chat input kapsayıcıları */
    [data-testid="stBottomBlockContainer"],
    .stChatFloatingInputContainer,
    .stChatInputContainer,
    .stTextInputContainer,
    .stChatInputRoot,
    .stChatInput,
    .stChatInput * {
        background: linear-gradient(180deg, #F5F0FF 0%, #F0E8F8 100%) !important;
        background-color: #F5F0FF !important;
    }

    /* Chat input çevresindeki son üç katmanı da soft lavanta yap */
    .stApp > div:nth-last-child(-n+3),
    .stApp > div:nth-last-child(-n+3) > *,
    .stApp > div:nth-last-child(-n+3) > * > * {
        background: linear-gradient(180deg, #F5F0FF 0%, #F0E8F8 100%) !important;
        background-color: #F5F0FF !important;
    }
    
    /* Genel input alanları */
    input, textarea {
        color: #4A4A4A !important;
    }
    
    /* Chat mesajları için özel stiller */
    [data-testid="stChatMessageContent"] {
        color: #4A4A4A !important;
    }
    
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] div,
    [data-testid="stChatMessageContent"] span {
        color: #4A4A4A !important;
    }
    
    /* Kullanıcı mesajları */
    [data-testid="stChatMessage"][data-message-role="user"] {
        color: #4A4A4A !important;
    }
    
    /* AI mesajları */
    [data-testid="stChatMessage"][data-message-role="assistant"] {
        color: #4A4A4A !important;
    }
    
    /* Tüm yazılar için genel kural */
    body, .main, .block-container {
        color: #4A4A4A !important;
    }
    
    /* Subheader ve başlıklar */
    .sub-header {
        color: #7A6A7A !important;
    }
    
    /* Footer */
    footer {
        color: #6A5A6A !important;
    }
    </style>
    <script>
    // Chat input container'ın arka planını soft lavanta yapmak için JavaScript
    function fixChatInputBackground() {
        const lavenderGradient = 'linear-gradient(180deg, #F5F0FF 0%, #F0E8F8 100%)';
        const lavenderColor = '#F5F0FF';
        
        // TÜM olası chat input container'ları bul
        const chatContainers = document.querySelectorAll('[data-testid="stChatInputContainer"], [data-testid="stChatInput"], .stChatFloatingInputContainer, .stChatInputContainer');
        
        chatContainers.forEach(chatContainer => {
            // Container'ı düzelt
            chatContainer.style.setProperty('background', lavenderGradient, 'important');
            chatContainer.style.setProperty('background-color', lavenderColor, 'important');
            
            // TÜM parent elementleri düzelt (body'ye kadar)
            let parent = chatContainer.parentElement;
            let depth = 0;
            while (parent && parent !== document.body && depth < 10) {
                parent.style.setProperty('background', lavenderGradient, 'important');
                parent.style.setProperty('background-color', lavenderColor, 'important');
                parent = parent.parentElement;
                depth++;
            }
            
            // TÜM child elementleri düzelt
            const allChildren = chatContainer.querySelectorAll('*');
            allChildren.forEach(child => {
                child.style.setProperty('background', lavenderGradient, 'important');
                child.style.setProperty('background-color', lavenderColor, 'important');
            });
        });
        
        // .stApp'in son child'ını bul ve düzelt
        const stApp = document.querySelector('.stApp');
        if (stApp) {
            const children = Array.from(stApp.children);
            const lastChild = children[children.length - 1];
            
            if (lastChild && lastChild.getAttribute('data-testid') !== 'stSidebar') {
                const fixElement = (element) => {
                    if (!element) return;
                    element.style.setProperty('background', lavenderGradient, 'important');
                    element.style.setProperty('background-color', lavenderColor, 'important');
                    Array.from(element.children).forEach(child => fixElement(child));
                };
                fixElement(lastChild);
            }
        }
        
        // TÜM div'leri kontrol et - chat input içeren veya yakınındaki tüm siyah div'leri düzelt
        const allDivs = document.querySelectorAll('div');
        allDivs.forEach(div => {
            const hasChatInput = div.querySelector('[data-testid="stChatInputContainer"]') || 
                                 div.querySelector('[data-testid="stChatInput"]') ||
                                 div.getAttribute('data-testid') === 'stChatInputContainer';
            
            if (hasChatInput) {
                div.style.setProperty('background', lavenderGradient, 'important');
                div.style.setProperty('background-color', lavenderColor, 'important');
                
                // Parent'ları da düzelt
                let parent = div.parentElement;
                let depth = 0;
                while (parent && parent !== document.body && depth < 5) {
                    parent.style.setProperty('background', lavenderGradient, 'important');
                    parent.style.setProperty('background-color', lavenderColor, 'important');
                    parent = parent.parentElement;
                    depth++;
                }
            }
        });
    }
    
    // Hemen çalıştır
    fixChatInputBackground();
    
    // Sayfa yüklendiğinde çalıştır
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixChatInputBackground);
    } else {
        fixChatInputBackground();
    }
    
    // MutationObserver ile dinamik değişiklikleri yakala
    const observer = new MutationObserver(() => {
        fixChatInputBackground();
    });
    observer.observe(document.body, { 
        childList: true, 
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class', 'data-testid']
    });
    
    // Her 100ms'de bir kontrol et (daha sık kontrol)
    setInterval(fixChatInputBackground, 100);
    </script>
""", unsafe_allow_html=True)

# Öneri gösterme fonksiyonu
def display_recommendation(recommendation: dict):
    """Öneriyi Streamlit'te göster"""
    if "error" in recommendation:
        st.error(f"❌ Hata: {recommendation['error']}")
        return
    
    if "kombinasyon" in recommendation:
        st.subheader("🎯 Önerilen Kombinasyon")
        
        for idx, item in enumerate(recommendation["kombinasyon"], 1):
            with st.expander(f"👕 Ürün {idx}: {item.get('urun_tanimi', 'Bilinmeyen Ürün')}", expanded=True):
                # Görsel varsa göster
                urun_gorsel = item.get('urun_gorsel', '')
                if urun_gorsel:
                    col_img, col_info = st.columns([1, 2])
                    with col_img:
                        try:
                            st.image(urun_gorsel, width=200, caption=item.get('urun_tanimi', ''))
                        except:
                            st.info("Görsel yüklenemedi")
                    with col_info:
                        st.write("**💰 Fiyat:**", item.get('urun_fiyat', 'Belirtilmemiş'))
                        st.write("**🔗 Link:**", item.get('urun_linki-href', item.get('urun_linki', 'Yok')))
                        st.write("**💡 Seçme Nedeni:**")
                        st.write(item.get('secme_nedeni', 'Açıklama yok'))
                        
                        if "onemli_ozellikler" in item:
                            st.write("**Önemli Özellikler:**")
                            for key, value in item["onemli_ozellikler"].items():
                                if value:
                                    st.write(f"• **{key.title()}:** {value}")
                else:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write("**💰 Fiyat:**", item.get('urun_fiyat', 'Belirtilmemiş'))
                        st.write("**🔗 Link:**", item.get('urun_linki-href', item.get('urun_linki', 'Yok')))
                        st.write("**💡 Seçme Nedeni:**")
                        st.write(item.get('secme_nedeni', 'Açıklama yok'))
                    
                    with col2:
                        if "onemli_ozellikler" in item:
                            st.write("**Önemli Özellikler:**")
                            for key, value in item["onemli_ozellikler"].items():
                                if value:
                                    st.write(f"• **{key.title()}:** {value}")
                
                urun_linki = item.get('urun_linki-href', item.get('urun_linki', ''))
                if urun_linki:
                    st.markdown(f"[🔗 Ürünü Görüntüle]({urun_linki})")
        
        st.divider()
        
        # Genel açıklama
        if "aciklama" in recommendation:
            st.info(f"📝 **Açıklama:** {recommendation['aciklama']}")
        
        # Stil notları
        if "stil_notlari" in recommendation:
            st.success(f"💡 **Stil Notları:** {recommendation['stil_notlari']}")
        
        # Uyum analizi
        if "uyum_analizi" in recommendation:
            with st.expander("🔍 Uyum Analizi"):
                st.write(recommendation['uyum_analizi'])
    else:
        st.info("Öneri hazırlanıyor...")

# Başlık - Barbie PNG (solda), DAPHNE (ortada), Barbie PNG (sağda, ters)
col_outer_left, col_outer_center, col_outer_right = st.columns([1, 2, 1])
with col_outer_center:
    # Görsel (solda), yazı (ortada), görsel (sağda, ters) - yan yana
    col_img_left, col_text, col_img_right = st.columns([0.7, 2, 0.7])
    
    # Sol görsel (normal)
    with col_img_left:
        try:
            barbie_image_path = "assets/barbie.png"
            if os.path.exists(barbie_image_path):
                st.image(barbie_image_path, width=85, use_container_width=False)
            else:
                st.markdown('<div style="text-align: center;"><p style="font-size: 2.5rem; margin: 0;">👑</p></div>', unsafe_allow_html=True)
        except:
            st.markdown('<div style="text-align: center;"><p style="font-size: 2.5rem; margin: 0;">👑</p></div>', unsafe_allow_html=True)
    
    # DAPHNE yazısı (ortada)
    with col_text:
        st.markdown('<h1 class="main-header" style="margin: 0; padding: 0; text-align: center; padding-left: 0.3rem; padding-right: 0.3rem;">DAPHNE</h1>', unsafe_allow_html=True)
    
    # Sağ görsel (ters - ayna efekti)
    with col_img_right:
        try:
            barbie_image_path = "assets/barbie.png"
            if os.path.exists(barbie_image_path):
                # Base64 encode ile görseli yükle ve ters çevir
                import base64
                with open(barbie_image_path, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode()
                    st.markdown(f"""
                        <div style='text-align: center;'>
                            <img src='data:image/png;base64,{img_data}' style='width: 85px; height: auto; transform: scaleX(-1); display: inline-block;' />
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<div style="text-align: center;"><p style="font-size: 2.5rem; margin: 0; transform: scaleX(-1); display: inline-block;">👑</p></div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown('<div style="text-align: center;"><p style="font-size: 2.5rem; margin: 0; transform: scaleX(-1); display: inline-block;">👑</p></div>', unsafe_allow_html=True)

# Sidebar - Prompt Önerileri
with st.sidebar:
    # Barbie PNG ve DAPHNE logosu
    try:
        # Görsel dosyasını yükle (assets klasöründe olmalı)
        barbie_image_path = "assets/barbie.png"
        if os.path.exists(barbie_image_path):
            st.image(barbie_image_path, use_container_width=True)
        else:
            # Eğer görsel yoksa placeholder
            st.markdown('<div style="text-align: center; padding: 1rem;"><p>👑</p></div>', unsafe_allow_html=True)
    except:
        st.markdown('<div style="text-align: center; padding: 1rem;"><p>👑</p></div>', unsafe_allow_html=True)
    
    # DAPHNE yazısı - görsele yakın
    st.markdown("""
        <div style='text-align: center; padding: 0.2rem 0 1rem 0;'>
            <h1 style='font-size: 2rem; font-weight: 700; color: #C8A2C8; margin: 0;'>DAPHNE</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### <span style='color: #C8A2C8;'>👗</span> Hızlı Öneriler", unsafe_allow_html=True)
    st.markdown("Aşağıdaki önerilerden birini seçerek hızlıca kombin isteyebilirsiniz:")
    
    prompt_suggestions = [
        "Toplantım var, şık bir kombin öner",
        "Günlük kullanım için rahat bir kombin",
        "İş görüşmesi için profesyonel kombin",
        "Yaz için hafif ve şık bir kombin",
        "Kış için sıcak tutan bir kombin"
    ]
    
    for suggestion in prompt_suggestions:
        if st.button(suggestion, key=f"suggestion_{suggestion}", use_container_width=True):
            st.session_state.selected_prompt = suggestion
            st.rerun()

# Varsayılan ayarlar (sabit) - Token tasarrufu için azaltıldı
provider = "groq"
model_choice = "llama-3.3-70b-versatile"
max_products = 10  # 15'ten 10'a düşürüldü (token tasarrufu)
max_reviews = 1  # 2'den 1'e düşürüldü (token tasarrufu)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.engine = None
    st.session_state.initialized = False
    st.session_state.current_model = None
    st.session_state.current_provider = None

# Provider veya model değiştiyse engine'i sıfırla
if (st.session_state.current_provider != provider or 
    st.session_state.current_model != model_choice):
    st.session_state.initialized = False
    st.session_state.engine = None
    st.session_state.current_provider = provider
    st.session_state.current_model = model_choice

# Engine'i başlat
if not st.session_state.initialized:
    with st.spinner("🔄 Veri setleri yükleniyor ve analiz ediliyor... Bu işlem birkaç dakika sürebilir."):
        try:
            st.session_state.engine = RecommendationEngine(
                "data/tum_urunler.xlsx",
                "data/tum_yorumlar.xlsx",
                model=model_choice,
                provider=provider
            )
            st.session_state.engine.initialize()
            st.session_state.initialized = True
            st.success("✓ Sistem hazır! 🎉")
            st.balloons()
        except FileNotFoundError as e:
            st.error(f"❌ Dosya bulunamadı: {str(e)}")
            st.info("Lütfen data/ klasöründe tum_urunler.xlsx ve tum_yorumlar.xlsx dosyalarının olduğundan emin olun.")
        except Exception as e:
            st.error(f"❌ Hata: {str(e)}")
            st.info("Lütfen hata mesajını kontrol edin ve gerekli ayarları yapın.")

# Seçilen prompt'u işle
if hasattr(st.session_state, 'selected_prompt') and st.session_state.selected_prompt:
    prompt = st.session_state.selected_prompt
    del st.session_state.selected_prompt
    # Prompt'u chat input gibi işle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # AI yanıtı
    if st.session_state.initialized and st.session_state.engine:
        with st.chat_message("assistant"):
            with st.spinner("🤔 Kombin önerisi hazırlanıyor... Bu işlem birkaç saniye sürebilir."):
                try:
                    recommendation = st.session_state.engine.get_recommendation(
                        prompt, 
                        product_limit=max_products,
                        review_limit=max_reviews
                    )
                    display_recommendation(recommendation)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": recommendation
                    })
                except Exception as e:
                    error_msg = f"❌ Bir hata oluştu: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": {"error": error_msg}
                    })

# Chat geçmişi
if st.session_state.messages:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                content = message["content"]
                # JSON formatında öneri göster
                if isinstance(content, dict) or (isinstance(content, str) and content.strip().startswith("{")):
                    try:
                        if isinstance(content, str):
                            rec = json.loads(content)
                        else:
                            rec = content
                        
                        display_recommendation(rec)
                    except json.JSONDecodeError:
                        st.markdown(content)
                else:
                    st.markdown(content)
            else:
                st.markdown(message["content"])

# Kullanıcı girişi
if prompt := st.chat_input("Kombin önerisi isteyin (örn: 'Toplantım var şık bir kombin öner', 'Günlük kullanım için rahat bir kombin')"):
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # AI yanıtı
    if st.session_state.initialized and st.session_state.engine:
        with st.chat_message("assistant"):
            with st.spinner("🤔 Kombin önerisi hazırlanıyor... Bu işlem birkaç saniye sürebilir."):
                try:
                    recommendation = st.session_state.engine.get_recommendation(
                        prompt, 
                        product_limit=max_products,
                        review_limit=max_reviews
                    )
                    
                    display_recommendation(recommendation)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": recommendation
                    })
                except Exception as e:
                    error_msg = f"❌ Bir hata oluştu: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": {"error": error_msg}
                    })
    else:
        st.warning("⚠️ Sistem henüz hazır değil. Lütfen bekleyin...")

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #7A6A7A; padding: 1rem; font-size: 0.9rem;'>
        <p>DAPHNE</p>
    </div>
""", unsafe_allow_html=True)
