# Multicast Yönlendirme

## Kapsam

Multicast, bant genişliği tasarrufu sağlamak amacıyla birden fazla ağ istemcisine tek bir akışın gönderilmesini sağlayan bir iletim tekniğidir. Radyo yayınları, video konferans gibi uygulamalar bu teknikten faydalanarak ağ alt yapısını daha etkin kullanabilirler.

## Menü yolu

- `Dinlenecek Ağ Arayüzleri > Statik RP Yönetimi`

## Kullanım adımları

1. BSR Adaylığı Önceliği ve RP Adaylığı Önceliği değerlerini belirleyin.
2. PIM Modu seçeneğini PIM-SSM - IGMPv3 olarak ayarlayın.
3. Ağ Arayüz IP Adresini 192.168.33.1-LAN1 olarak girin.
4. Uzaklık değerini 64 olarak ayarlayın.
5. Açıklama alanına MULTICAST YÖNLENDİRME yazın.
6. Kaydet butonuna tıklayarak yapılandırmayı kaydedin.
7. Aktif durumu seçmek için checkbox'ı işaretleyin.
8. Ağ Arayüz IP Adresi seçeneğini kullanarak bir ağ arayüzü seçin.

## Alanlar

- `BSR Adaylığı Önceliği` (Otomatik BSR - RP Ayarları): BSR (Bootstrap Router) adayı için öncelik değeri.
- `RP Adaylığı Önceliği` (Otomatik BSR - RP Ayarları): RP (Rendezvous Point) adayı için öncelik değeri.
- `PIM Modu` (Durum paneli): Ağ arayüzünün PIM modunu seçer.
- `Ağ Arayüz IP Adresi` (Durum paneli): Ağ arayüzünün IP adresini girer.
- `Uzaklık` (Durum paneli): Ağ arayüzünün uzaklığını belirler.
- `Açıklama` (Durum paneli): Ağ arayüzüne bir açıklama girer.
- `Durum` (Statik RP Yönetimi - Yeni Kayıt paneli): Durum

## Görünür kontroller

- `Yenile`: Ekrandaki bilgileri yeniden yükleme işlemi başlatır.
- `+ Ekle`: Yeni bir ağ arayüzü eklemek için kullanılır.
- `Durum`: Ağ arayüzünün aktif olup olmadığını belirler.
- `İptal`: Ekrandaki işlemleri iptal etmek için kullanılır.
- `Kaydet`: Ağ arayüzü yapılandırmasını kaydetmek için kullanılır.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/yonlendirme-yonetimi/multicast-yonlendirme/
- Güven puanı: 0.94
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
