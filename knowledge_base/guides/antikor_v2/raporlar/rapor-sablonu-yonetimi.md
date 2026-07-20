# Rapor Şablonu Yönetimi

## Kapsam

Bu doküman, rapor şablonlarının yönetimi ile ilgili adımları ve ayarları açıklamaktadır.

## Menü yolu

- `Şablon Ayarları > Sorgu Oluştur > Grafik Ayarları`
- `1. Şablon Ayarları > Sorgu Oluştur > Grafik Ayarları`

## Kullanım adımları

1. Anti-Spam Raporları
2. Cluster Raporları
3. Dışa Atılan İstek Raporları
4. DNS Filtreleme Raporları
5. Doğrulama Raporları
6. Güvenlik Kuralları Kullanım Raporları
7. Hotspot Raporları
8. IPSec Servis Raporları
9. Paket Filtreleme Raporları
10. PPP Debug Raporları
11. PPP Raporları
12. AV, AppID, IPS, DoS Raporları
13. SSH Denetimi Raporları
14. SSH Koruma Raporları
15. SSL VPN Raporları
16. Sanal Kablo Raporları
17. Web Erişim Raporları
18. Web Sunucu Güvenliği Raporları
19. WF İçerik ve Antivirüs Tarama Raporları
20. WF Sayfa Yasaklama Raporları
21. Yasaklanan Kullanıcılar Raporları
22. Şablon Ayarları
23. Sorgu Oluştur
24. Grafik Ayarları
25. Bu alanlar doldurulduktan sonra İleri butonuna tıklanarak ikinci adıma geçilir.
26. SELECT – Kolonlar ve Fonksiyonlar
27. GROUP BY – Gruplama
28. HAVING – Grup Filtreleme
29. WHERE – Koşullar
30. ORDER BY – Sıralama
31. LIMIT / OFFSET
32. Grafik ayarlarını yapılandırın.
33. Seçilen grafik türünü onaylayın.

## Alanlar

- `Şablona Adı` (Şablona Adı): Rapor şablonunun adını girer.
- `Rapor Çıkış Türü` (Rapor Çıkış Türü): Rapor çalıştırıldığında oluşturulacak dosya formatı.
- `Saklama Süresi (Gün)` (Saklama Süresi): Eski raporlar bu süre sonunda otomatik silinir (1-365 gün).
- `Tarih` ([SELECT – Kolonlar ve Fonksiyonlar]): Raporda gösterilecek tarih seçilir.
- `Saat` ([SELECT – Kolonlar ve Fonksiyonlar]): Raporda gösterilecek saat seçilir.
- `Hafta` ([SELECT – Kolonlar ve Fonksiyonlar]): Raporda gösterilecek hafta seçilir.
- `Ay` ([SELECT – Kolonlar ve Fonksiyonlar]): Raporda gösterilecek ay seçilir.
- `Yıl` ([SELECT – Kolonlar ve Fonksiyonlar]): Raporda gösterilecek yıl seçilir.
- `WHERE Koşulları` (WHERE - Koşullar): Rapor verilerinin filtrelenmesi için kullanılan koşul.
- `ORDER BY – Sıralama` (ORDER BY - Sıralama): Sonuçların sıralanmasını sağlamak için kullanılan sütun adı veya ifade.
- `Grafik Türü` (Grafik Ayarları paneli): Rapor çıktısında kullanılacak grafik türünü seçmek için kullanılır.

## Görünür kontroller

- `Durum`: Rapor şablonunun aktif olup olmadığını belirler.
- `SMTP Ayarı (Opsiyonel)`: SMTP seçilmemesi zamanlama yapılamaz. Sadece manuel çalıştırma yapılabilir.
- `Tümünü Seç`: Mevcut kolonların tümü seçilir.
- `Temizle`: Seçilen kolonları temizler.
- `+ Koşul Ekle`: Rapor verilerinin filtrelenmesi için koşul eklemek için kullanılan düğme.
- `+ Sıralama Ekle`: Sonuçların sıralanmasını sağlamak için sıralama eklemek için kullanılan düğme.
- `Geri Dön`: Önceki adıma geri dönülmesi için kullanılır.
- `Geri`: Önceki adıma geri dönülmesi için kullanılır.
- `Tamamla`: Grafik ayarlarını onaylayarak sonraki adıma geçilmesi için kullanılır.

## Uyarılar

- SMTP ayarı seçilmezse rapor zamanlanamaz, yalnızca manuel olarak çalıştırılabilir.
- Bu tabloda 1 adet index mevcut. Performanslı sorgular için index'li kolonları WHERE koşullarında kullanın.
- Aggregation fonksiyonları (COUNT, SUM, AVG, vb.) kullanmak için en az bir kolon seçin.
- HAVING kullanmak için GROUP BY gereklidir.
- Once SELECT te kolon seçin ve GROUP BY ekleyin, sonra aggregation fonksiyonları ekleyin.
- Saat, Hafta, Ay ve Yıl kontrolüne tıkladığınızda hangi verilerin gruplandığına dair belirtilmemiş.
- GROUP BY - Gruplama bölümünde hangi verilerin gruplandığına dair belirtilmemiş.
- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: Rapor Çıkış Türü, Saklama Süresi (Gün), Şablona Adı

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/raporlar/rapor-sablonu-yonetimi/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
