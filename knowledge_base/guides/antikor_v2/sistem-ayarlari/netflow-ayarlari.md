# Netflow Ayarları

## Kapsam

Netflow, IP trafik bilgisini toplayan network protokolüdür.  Antikor, üzerinden geçen bütün trafiğin data başlıklarını, istenilen bir netflow collector’a (toplayıcıya) yollayabilir. Buradan internet trafik analizi yapılabilir. Network kısmından LAN, WAN ve DMZ arayüzleri seçilebilir.

## Menü yolu

- `Netflow Ayarları`

## Kullanım adımları

1. Durum
2. Adres Ailesi
3. IP Adresi
4. Portu
5. BPF Filtre İfadesi
6. Network
7. işlemler
8. Durum seçeneğini aktif hale getirin.
9. Adres Ailesi seçeneğini IPv4 olarak ayarlayın.

## Alanlar

- `#` (Durum): Sayısal bir sütun başlığı. Veri yoksa boş bırakılmalıdır.
- `Durum` (Durum): Netflow ayarının durumu. Veri yoksa boş bırakılmalıdır.
- `Adres Ailesi` (Adres Ailesi): IP adresinin ailesi. Veri yoksa boş bırakılmalıdır.
- `IP Adresi` (IP Adresi): Netflow ayarının IP adresi. Veri yoksa boş bırakılmalıdır.
- `Portu` (Portu): Netflow ayarının port numarası. Veri yoksa boş bırakılmalıdır.
- `BPF Filtre İfadesi` (BPF Filtre İfadesi): Netflow ayarının BPF filtre ifadesi. Veri yoksa boş bırakılmalıdır.
- `Network` (Network): Netflow ayarının ağ bilgisi. Veri yoksa boş bırakılmalıdır.
- `işlemler` (işlemler): Netflow ayarının işlemlerini gösteren bir sütun başlığı. Veri yoksa boş bırakılmalıdır.
- `BPF Filtre ifadesi` (BPF Filtre ifadesi): Netflow filtre ifadesini girilir.

## Görünür kontroller

- `Yenile`: Ekrandaki verileri yeniden yükleme.
- `Ekle`: Yeni bir netflow ayarını eklemek için kullanılan düğme.
- `Göster/Gizle`: Gösterilen verileri gizleme veya gösterme seçenekleri.
- `Tamam`: Ekrandaki ayarları onaylamak için kullanılan düğme.
- `Filtrele`: Gösterilen verileri filtrelemek için kullanılan düğme.
- `Filtreyi Temizle`: Verilerin temizlenmesini ve filtrelerin sıfırlanmasını sağlar.
- `Durum`: Netflow ayarlarının aktif olup olmadığını belirler.
- `Adres Ailesi`: IPv4 veya IPv6 adres ailesini seçer.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/sistem-ayarlari/netflow-ayarlari/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
