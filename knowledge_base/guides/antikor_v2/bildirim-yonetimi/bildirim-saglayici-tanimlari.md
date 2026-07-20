# Bildirim Sağlayıcı Tanımları

## Kapsam

Antikor NGFW kayıt servisi aktif olduğunda, kayıt formunu dolduran kullanıcılara sistem otomatik olarak bir onay kodu (SMS) gönderebilir.

## Menü yolu

- `SMS Sağlayıcıları > SMS Ayarları > Mail Ayarları`
- `SMS Ayarları > SMS Sağlayıcıları`
- `SMS Sağlayıcıları > SMS Ayarları > Bildirim Ayarları (SMS, Eposta) - Yeni Kayıt`
- `SMS Ayarları > Bildirim Sağlayıcı Tanımları - Yeni Kayıt`
- `SMS Sağlayıcılar > SMS Ayarları > Mail Ayarları`
- `Mail Ayarları Yeni Kayıt`

## Kullanım adımları

1. SMS sağlayıcısı listesini görüntülemek için 'SMS Sağlayıcıları' seçeneğini kullanın.
2. Yeni bir SMS sağlayıcısı eklemek için '+ Ekle' butonuna tıklayın.
3. SMS Sağlayıcıları menüsünü seçin.
4. Yeni bir SMS sağlayıcısı ekleme için '+ Ekle' düğmesine tıklayın.
5. Adı alanında SMS sağlayıcısının adını girin.
6. Metod seçeneğini 'GET' olarak belirleyin veya başka bir yöntem seçeneği kullanabilirsiniz.
7. Url alanında SMS gönderimi için kullanılan URL adresini girin.
8. SMS sağlayıcısından alınan kullanıcı adı ve şifresi bu menüde tanımlanmalıdır.
9. Kullanıcı adını girin.
10. Sunucu bilgilerini girin.
11. Port numarasını belirtin.
12. Kullanıcı adınızı girin.
13. Güvenlik türünü seçin.
14. Test Et butonuna tıklayarak SMTP sunucusunun erişimini test edin.
15. Test Et butonuna tıklayın.
16. Mail gönderme işleminin başarıyla tamamlanması
17. Sunucu alanına SMTP sunucusunun adını veya IP adresini girin.
18. Port alanına SMTP sunucusundaki port numarasını girin (varsayılan 465).
19. SSL, TLS ve Yok seçeneklerinden birini işaretleyin.
20. SMTP Auth seçeneğini işaretleyin.
21. Kullanıcı Adı, Parola, Gönderici Adı, Gönderici Adresi ve Açıklama alanlarını gerekli bilgilerle doldurun.
22. Kaydet butonuna tıklayarak ayarları kaydedin.

## Alanlar

- `Adı` (SMS Sağlayıcıları paneli): SMS sağlayıcısının adını içeren metin alanları.
- `Metod` (SMS Sağlayıcıları paneli): SMS gönderiminde kullanılan yöntemleri içeren metin alanları.
- `Url` (SMS Sağlayıcıları paneli): SMS gönderimine yönelik URL'leri içeren metin alanları.
- `Başarılı Cevap Kodu` (SMS Sağlayıcıları paneli): SMS gönderimi başarılı olduğunda alacağı cevap kodlarını içeren metin alanları.
- `Geçersiz Karakterler` (SMS Sağlayıcıları paneli): SMS gönderiminde geçersiz karakterleri içeren metin alanları.
- `Sağlayıcı Adı` (SMS Ayarları paneli): SMS sağlayıcısının adını girin.
- `Kullanıcı Adı` (SMS Ayarları paneli): SMS sağlayıcısından alınan kullanıcı adını girin.
- `Gönderici Başlığı` (SMS Ayarları paneli): SMS göndericisi başlığını girin.
- `Sms Sağlayıcı` (İleti Merkezi): SMS sağlayıcısı seçimi
- `Parola` (Parola): SMS sağlayıcısından alınan şifre
- `Sunucu` (Sunucu sütunu): SMTP sunucusunun adı veya adresi.
- `Port` (Port sütunu): SMTP sunucusunun port numarası.
- `Güvenlik Türü` (Güvenlik Türü sütunu): SMTP sunucusunun güvenlik türü (SSL, TLS veya Yok).
- `Gönderici Adı` (Sunucu): SMTP gönderici adınızı girin. Varsayılan olarak boş bırakılabilir.
- `Gönderici Adresi` (Sunucu): SMTP gönderici adresini girin. Varsayılan olarak boş bırakılabilir.
- `Açıklama` (Sunucu): Bildirim sağlayıcısı hakkında ek bilgileri girin. Varsayılan olarak boş bırakılabilir.

## Görünür kontroller

- `Yenile`: Listeyi yeniden yüklemek için kullanılan buton.
- `+ Ekle`: Yeni bir SMS sağlayıcısı eklemek için kullanılan buton.
- `İptal`: Ekrandaki işlemlerin iptali için kullanılır.
- `Kaydet`: Ekranda yapılan değişiklikleri kaydeden ve ekrandan çıkmanızı sağlayan butondur.
- `Ekle`: Yeni bir SMS sağlayıcısı eklemek için kullanılır.
- `Test Et`: SMTP servis bilgilerinin doğruluğunu ve SMTP sunucusuna erişim kontrol eden buton.
- `OK`: İşlemi onaylamak için kullanılan düğme
- `Sunucu`: SMTP sunucusunun adını veya IP adresini belirtir.
- `Port`: SMTP sunucusundaki port numarasını belirtir. Varsayılan 465.
- `SSL`: SMTP sunucusunda SSL kullanılsın mı?
- `TLS`: SMTP sunucusunda TLS kullanılsın mı?
- `Yok`: SMTP sunucusunda SSL veya TLS kullanılmazsa bu seçeneği işaretleyin.
- `SMTP Auth`: SMTP doğrulaması kullanılsın mı?

## Uyarılar

- Adı ve Url alanları boş bırakılamaz. Bu alanlarda girdi yapmadığınızda, kaydet butonu etkin olmayacaktır.
- SMTP sunucusu ve port numarası doğru olmalıdır.
- Kullanıcı adı ve şifre doğru olmalıdır.
- Güvenlik türü seçeneği doğru olmalıdır.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/bildirim-yonetimi/bildirim-saglayici-tanimlari/
- Güven puanı: 0.94
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
