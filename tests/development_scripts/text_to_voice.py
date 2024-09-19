# Import the required module for text 
# to speech conversion
from gtts import gTTS

# The text that you want to convert to audio
alert_messages = [
    "Dikkat! Malzeme Deposunda başınızın üzerinde ağır kutular olabilir. Güvende kalmak için lütfen baretinizi takmayı unutmayın. Unutmayın, bir anlık ihmal büyük sorunlara yol açabilir.",
    "Montaj Bölümünde başınızın üzerinden geçen parçalara dikkat! Baretiniz sizi bu parçalardan korur, lütfen takmayı ihmal etmeyin.",
    "Yüksek Raflar Alanında çalışırken yukarıdan düşebilecek küçük ama tehlikeli objelere dikkat edin. Baretiniz bu tür risklere karşı en iyi savunmanızdır, lütfen takın."
]

thank_you_messages = [
    "Baretini takmayı ihmal etmediğini gördüm, harikasın! Güvenliğin bizim için ne kadar önemli olduğunu gösteriyorsun.",
    "Baretini taktığını biliyorum, bu konuda gösterdiğin dikkate teşekkürler! Hepimizin güvenliği senin gibi bilinçli çalışanlarla sağlanıyor.",
    "Baretinle sahada olduğunu fark ettim, teşekkür ederim! Güvenlik bilincinle hepimize örnek oluyorsun."
]

for text_no, text in enumerate(alert_messages):
    # Language in which you want to convert
    language = 'tr'

    # Convert text to speech
    myobj = gTTS(text=text, lang=language, slow=False)
    myobj.save(f"alert_{text_no}.mp3")

for text_no, text in enumerate(thank_you_messages):
    # Language in which you want to convert
    language = 'tr'

    # Convert text to speech
    myobj = gTTS(text=text, lang=language, slow=False)
    myobj.save(f"thank_you_{text_no}.mp3")