# SysLog Ayarları

## Kapsam

Sunucu sistem loglarının kayıt edileceği sunucunun/sunucuların eklendiği bölümdür. 26 farklı log çeşidi ve 7 farklı log formatını desteklemektedir. Tercih edilen ham veya yapısal log formatlarında kullanıcının sağlayacağı log toplayıcısına veya SIEM’e iletilebilmektedir.

## Kullanım adımları

1. Durum ve Açıklama alanlarını kullanarak logun durumu ve açıklamasını ayarlayın.
2. Log Çeşitleri alanından uygun log türünü seçin.
3. Filtre Metni alanına log filtresi metnini girin (seçeneğe göre).
4. Gönderim Formatı alanına log gönderim formatını girin (seçeneğe göre).
5. Sunucu Adresi, Protokol ve Port alanlarını uygun değerlerle doldurun.
6. İşlemler alanından log ayarlarını düzenlemek veya silmek için gerekli butonları kullanın.
7. Durum'u aktif olarak ayarlayın.
8. Log Çeşitleri seçimi yapın.
9. Filtre Metni alanına gerekli metni girin.
10. Gönderim Formatı'ndaki seçenekler arasından birini seçin.
11. Sunucu Adresi alanına IPv4 adresini girin.
12. Adres Ailesi'nde IPv4 seçeneğini işaretleyin.
13. Port numarasını '514' olarak ayarlayın.
14. Durum seçeneğini aktif olarak ayarlayın.
15. Açıklama alanına gerekli bilgileri girin.
16. Log Çeşitleri seçeneğini belirleyin.
17. Gönderim Formatı alanına gerekli formatı girin.
18. Adres Ailesi alanına gerekli adres ailesini girin.
19. Sunucu Adresi alanına gerekli sunucu adresini girin.
20. Protokol seçeneğini UDP olarak ayarlayın.
21. Port alanına 514 değerini girin.
22. Kaydet butonuna tıklayarak kaydedin.
23. Durum alanındaki checkbox'ın durumu aktif hale getirin.
24. Açıklama alanına gerekli açıklama metni girin.
25. Log Çeşitleri seçeneğini kullanarak log türünü seçin.
26. Filtre Metni alanına uygulamak istediğiniz filtre metni girin.
27. Gönderim Formatı seçeneğini kullanarak gönderim formatını seçin.

## Alanlar

- `Durum` (Durum sütunu): Logun durumu seçmek için.
- `Açıklama` (Açıklama sütunu): Logun açıklaması girilebilir.
- `Log Çeşitleri` (Log Çeşitleri sütunu): Log türünü seçmek için.
- `Filtre Metni` (Filtre Metni sütunu): Log filtresi metni girilebilir.
- `Gönderim Formatı` (Gönderim Formatı sütunu): Log gönderim formatı girilebilir.
- `Sunucu Adresi` (Sunucu Adresi sütunu): Log sunucusu adresi girilebilir.
- `Protokol` (Protokol sütunu): Log protokolü girilebilir.
- `Port` (Port sütunu): Log portu girilebilir.
- `İşlemler` (İşlemler sütunu): Log işlemlerini yönetmek için.
- `Adres Ailesi` (Adres Ailesi): IPv4 veya IPv6 arasından seçebilirsiniz. Şu anda IPv4 seçili.

## Görünür kontroller

- `Yenile`: Ekrandaki verileri yeniden yükleme.
- `Ekle`: Yeni bir log ayar eklemek için.
- `Göster/Gizle`: Verileri göstere veya gizleme.
- `Tamam`: Ekrandaki ayarları kaydetmek için.
- `Filtrele`: Verileri filtrelemek için.
- `Filtreyi Temizle`: Filtreleri temizlemek için.
- `Durum`: Aktif
- `İptal`: İptal
- `Kaydet`: Kaydet

## Uyarılar

- Log türleri ve gönderim formatları seçimi doğru olmalıdır. Yanlış seçim yapabilirsiniz.
- Log gönderim formatı 'Ham Kayıt' seçildiğinde, sunucu logları doğrudan sunucuya gönderilir. Bu durumda, sunucunun IPv4 adresini doğru bir şekilde girin.
- Log gönderim formatı 'Ham Kayıt' seçildiğinde, port numarasını doğru bir şekilde ayarlayın.
- Eğer kaydet düğmesi tuşlanmazsa, kontrol edilmesi gereken bir hata veya eksiklik olabilir. Lütfen ekranın altındaki mesajları kontrol edin.
- Log Çeşitleri seçimi için kullanılacak log türünün listesi belirtilmemiş. Bu nedenle, hangi log türünü seçeceğinizi belirtmek mümkün değil.
- Filtre Metni alanına gerekli metnin girilmesi durumunda, hangi filtrelerin uygulanacağını belirlemek mümkün değil.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/sistem-ayarlari/syslog-ayarlari/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
