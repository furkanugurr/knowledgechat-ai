# Log Yönetimi - ePati Siber Güvenlik

## Kapsam

title: log yonetimi —

## Kullanım adımları

1. Web Erişim Raporları (Http / Https / Proxy) log bilgilerini sorgulamak için 'Sorgulanabilir Gün' ve 'Sorgulanabilir Boyut' alanlarını kontrol edin.
2. Hotspot Logları, DHCPv4 Logları gibi log türlerinin arşivlenme durumunu ve boyutunu 'Arşivlenmiş Gün', 'Arşivlenmiş Boyut' alanlarında kontrol edin.

## Alanlar

- `Log Türü` (Log Yönetimi Tablosu): Sistem üzerinde tutulan log türlerinin isimleri. Örneğin, 'Web Erişim Raporları', 'Hotspot Logları' gibi.
- `Sorgulanabilir Gün` (Log Yönetimi Tablosu): Veritabanında sorgulanabilecek log bilgilerinin gün sayısını gösterir. Örneğin, '2' veya '-1'.
- `Sorgulanabilir Boyut` (Log Yönetimi Tablosu): Veritabanında sorgulanabilecek log bilgilerinin boyutunu gösterir. Örneğin, '472 kB' veya '0 bytes'.
- `Arşivlenmiş Gün` (Log Yönetimi Tablosu): Arşivlenmiş log bilgilerinin gün sayısını gösterir. Örneğin, '2' veya '-1'.
- `Arşivlenmiş Boyut` (Log Yönetimi Tablosu): Arşivlenmiş log bilgilerinin boyutunu gösterir. Örneğin, '416 kB' veya '0 bytes'.

## Görünür kontroller

- `Veritabanı Temizle`: Veritabanındaki log bilgilerini temizleme işlemi başlatır.
- `Arşiv Temizle`: Arşivlenmiş log bilgilerini temizleme işlemi başlatır.

## Uyarılar

- Sorgulanabilir ve arşivlenmiş log bilgileri, veritabanında ve arşivde tutulur. Log türlerine göre sorgulanabilirlik ve arşivlenme süreleri değişebilir.
- Veritabanı temizleme ve arşiv temizleme işlemlerini başlatmak için 'Veritabanı Temizle' ve 'Arşiv Temizle' butonlarını kullanın.
- DHCPv6 Logları, Sistem Logları gibi bazı log türleri sorgulanabilirlik ve arşivlenme sürelerini belirlemek için daha fazla bilgi gerektirebilir.
- Sistem üzerinde tutulan log türlerinin tam listesi ve özellikleri hakkında daha fazla bilgi almak için 'Yapılandırma Örnekleri' veya 'Terimler Sözlüğü' başlıkları altında bulunan detaylı bilgileri inceleyin.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/raporlar/log-yonetimi/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
