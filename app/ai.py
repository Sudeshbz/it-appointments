# app/ai.py
import pickle
import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

MODEL_PATH = "model.pkl"

# Örnek eğitim verisi (Sanki geçmiş verilerden öğrenmiş gibi)
train_data = [
    ("Bilgisayarım açılmıyor mavi ekran", "Donanım"),
    ("Ekran kırıldı görüntü gelmiyor", "Donanım"),
    ("Mouse çalışmıyor", "Donanım"),
    ("Yazıcı kağıt sıkıştırdı", "Donanım"),
    ("İnternet çok yavaş girmiyor", "Ağ"),
    ("Wifi şifresini unuttum", "Ağ"),
    ("VPN bağlanmıyor hata veriyor", "Ağ"),
    ("Outlook şifremi unuttum", "Yazılım"),
    ("Excel dosyası açılmıyor", "Yazılım"),
    ("Virüs programı uyarı veriyor", "Yazılım"),
]

def train_and_save_model():
    """Basit bir NLP modelini eğitir ve dosyaya kaydeder."""
    texts, labels = zip(*train_data)
    
    # Kelime sayısına dayalı basit bir Naive Bayes modeli
    model = make_pipeline(CountVectorizer(), MultinomialNB())
    model.fit(texts, labels)
    
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print("AI Modeli eğitildi ve kaydedildi.")

def load_model():
    """Eğitilmiş modeli yükler."""
    if not os.path.exists(MODEL_PATH):
        train_and_save_model()
        
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

def predict_category(text: str) -> str:
    """Gelen metni analiz edip kategori (Donanım, Yazılım, Ağ) döndürür."""
    model = load_model()
    prediction = model.predict([text])
    return prediction[0]

if __name__ == "__main__":
    # Bu dosyayı doğrudan çalıştırırsan test eder
    train_and_save_model()
    print(predict_category("Bilgisayarım çok ısınıyor"))