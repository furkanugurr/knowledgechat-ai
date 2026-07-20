# Güvenilir Proxy Sunucuları (XFF)

## Kapsam

Antikor ve istemcinin arasında yer almasını istenilen, istemcinin gönderdiği istekleri doğrulayan ve yönlendiren iletişim sunucusunun (Proxy) IP adresi bu bölüme işlenmektedir. Temel olarak trafikte hangi XFF başlığına(X-Fowarded-For header) güvenileceği belirlenmektedir.

## Menü yolu

- `Güvenilir Proxy Sunucuları (XFF) > Yeni Kayıt`

## Kullanım adımları

1. + Ekle
2. Git
3. Durum seçeneğini aktif olarak ayarlayın veya pasif olarak bırakın.
4. Proxy sunucusuna ait açıklama yapın.
5. Kayıtları kaydetmek için 'Kaydet' butonuna tıklayın.
6. Durum seçeneğini aktif hale getirin veya devre dışı bırakın.
7. Adres Ailesi seçeneğini IPv4 olarak ayarlayın.

## Alanlar

- `Göster/Gizle` (Güvenilir Proxy Sunucuları (XFF) paneli): Liste gösterimini gizlemek veya gösterebilmek için kullanılan düşüm
- `Sayfa Başı Kayıt Sayısı` (Güvenilir Proxy Sunucuları (XFF) paneli): Liste sayfasındaki kayıtların sayısı belirlemek için kullanılan düşüm
- `Tamam` (Güvenilir Proxy Sunucuları (XFF) paneli): Listeyi tam olarak gösterebilmek için kullanılan düşüm
- `Filtrele` (Güvenilir Proxy Sunucuları (XFF) paneli): Listeyi filtrelemek için kullanılan düşüm
- `Filtreyi Temizle` (Güvenilir Proxy Sunucuları (XFF) paneli): Filtreleri temizlemek için kullanılan düğme
- `Sunucu IP Adresleri` (Sunucu IP Adresleri): Proxy sunucusunun IP adreslerini girin.
- `Açıklama` (Açıklama): Proxy sunucusuna ait açıklama yapın.
- `IP Bloğu` (IPv4): IPv4 bloğunu girerken kullanılır.
- `Çıkış IP Adresi` (Çıkış IP Adresi): Proxy sunucusunun çıkış IP adresini girerken kullanılır.

## Görünür kontroller

- `+ Ekle`: Yeni proxy sunucusu eklemek için kullanılan düğme
- `Git`: Ekrandaki formu kaydetmek için kullanılan düğme
- `Durum`: Proxy sunucusunun aktif olup olmadığını belirler.
- `İptal`: Ekrandaki işlemleri iptal etmek için kullanılır.
- `Kaydet`: Kayıtları kaydetmek için kullanılır.
- `Adres Ailesi`: Proxy sunucusu için IPv4 veya IPv6 adres ailesini seçer.

## Uyarılar

- UYARI: Bilinmeyen kaynaklara izin verilmesi halinde, saldırıgın, X-Forwarded-For başlığı kullanarak IP spoofing saldırısı gerçekleştirilebilir.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/web-filtreleme/guvenilir-proxy-sunuculari-xff/
- Güven puanı: 0.94
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
