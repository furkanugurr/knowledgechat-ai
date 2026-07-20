# LLDP Ayarları

## Kapsam

LLDP, ağlarda kendi makinemizin komşularına yayınladıkları ve komşuları hakkında bilgi sahibi oldukları standart bir metoddur. LLDP bağlantısı için ayarlar bu menüde yapılmaktadır. Gerekli ayarlar yapıldıktan sonra Anlık Gözlem menüsü altında bulunan LLDP Durumu ndan gözlem yapılabilmektedir.

## Menü yolu

- `LLDP Ayarları > LLDP Durumu`
- `epati (config) #`

## Kullanım adımları

1. Networkler seçeneğini belirleyin ve 'Kaydet' butonuna tıklayın.
2. lldp run
3. show lldp info remote-device

## Alanlar

- `Networkler` (LLDP Ayarları paneli): Ağlarda kullanılan networkleri seçmek için düşey menü.
- `Sistem Adı` (LLDP Ayarları paneli): Sisteme ait bir ad belirlemek için metin alan.
- `Sistem Açıklaması` (LLDP Ayarları paneli): Sisteme ait bir açıklama yazmak için metin alan.
- `LocalPort` (LLDP Remote Devices Information): Yerel port numarasını seçer.
- `ChassisId` (LLDP Remote Devices Information): Kasayı tanımlar.
- `PortId` (LLDP Remote Devices Information): Port ID'sini gösterir.
- `PortDescr` (LLDP Remote Devices Information): Port açıklamasını gösterir.
- `SysName` (LLDP Remote Devices Information): Sistem adını gösterir.

## Görünür kontroller

- `Kaydet`: Ayarları kaydeden ve tanımları uyguladığını belirten buton.
- `lldp run`: LLDP bağlantısını başlatır.
- `show lldp info remote-device`: Komşu cihaz hakkında bilgi alır.

## Uyarılar

- Ayarları kaydedip, tanımları uyguladıktan sonra LLDP Durumu sayfasından gözlem yapabilirsiniz.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/sistem-ayarlari/lldp-ayarlari/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
