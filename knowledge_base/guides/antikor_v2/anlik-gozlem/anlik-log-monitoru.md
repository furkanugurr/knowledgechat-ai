# Anlık Log Monitörü

## Kapsam

Bu doküman, DMZ Trafik Logları ve Güvenlik Kuralları loglarının cihazda tutulması için gerekli adımları açıklamaktadır.

## Menü yolu

- `Sistem Ayarları > Log Ayarları > Paket Filtreleme Logları`
- `Sistem Ayarları > Log Ayarları`
- `DMZ Yönetimi > DMZ Sunucu Yönetimi`
- `Sistem Ayarları > Log Ayarları > Paket Filtreleme Logları > DMZ Yönetimi > DMZ Sunucu Yönetimi`

## Kullanım adımları

1. Yönetim Paneli Erişim Log çıktıları resimde görüleceği gibi görüntülenecektir.
2. DMZ Trafik Logları monitörde gözlemlenmek isteniyorsa sırasıyla, Sistem Ayarları > Log Ayarları > Paket Filtreleme Logları cihazda tut seçilir.
3. Sistem Ayarları > Log Ayarları > Paket Filtreleme Logları > Cihazda Tut
4. DMZ Yönetimi > DMZ Sunucu Yönetimi > Erişimlere tıklanır. Erişimler içerisindeki kurallardan logu tutulacak kural düzenle tıklanır.
5. Durum: Aktif
6. DMZ Türü: NAT Yapma, Olduğu Gibi Erişim
7. Adres Ailesi: IPv4
8. DMZ IP Arayüzü: Seçenek
9. DMZ IP Adresi: Seçenek
10. Loglama: Aktif
11. Erişim Denetimi: Bu Ekrandan Yönet
12. Güvenlik Kuralları logları için sırasıyla, Sistem Ayarları > Log Ayarları > Paket Filtreleme Logları cihazda tut seçilir.
13. Güvenlik kurallarında log tutulması istenilen kuralda Loglama etkinleştirilir.
14. Loglama etkinleştirildikten sonra, log tutulması istenilen diğer servislerde Trafiği Logla seçeneği olmayan menülerde, servisin açılması yeterlidir.

## Alanlar

- `Filtre (Düzenli ifade)` (Parametreler paneli): Log filtreleme için düzenli ifade girilmesi
- `Açıklama` (Açıklama): DMZ sunucusunun açıklamasını girer.
- `Kaynak Güvenlik Bölgesi` (IP Kuralları): Loglama için kaynak güvenlik bölgesini belirtir.
- `Kaynak Adres` (IP Kuralları): Loglama için kaynak adresini belirtir.
- `Hedef Güvenlik Bölgesi` (IP Kuralları): Loglama için hedef güvenlik bölgesini belirtir.
- `Hedef Adres` (IP Kuralları): Loglama için hedef adresini belirtir.
- `Servisler` (IP Kuralları): Loglama için servisleri belirtir.

## Görünür kontroller

- `Durdur`: Logları durdurma
- `Temizle`: Logları temizleme
- `SSH Denetimi Logları`: SSH denetimini cihazda tutma seçeneği.
- `Web Filtreleme - Sayfa Yasaklama Logları`: Web filtreleme sayfa yasaklamalarını cihazda tutma seçeneği.
- `Web Uygulama Güvenliği Logları`: Web uygulama güvenliğini cihazda tutma seçeneği.
- `AV, AppID, IPS, DoS Logları`: Antivirüs, AppID, IPS ve DoS loglarını cihazda tutma seçeneği.
- `DNS Filtreleme Logları`: DNS filtreleme loglarını cihazda tutma seçeneği.
- `PPP Logları`: PPP loglarını cihazda tutma seçeneği.
- `PPP Debug Logları`: PPP debug loglarını cihazda tutma seçeneği.
- `Sanal Kablo Logları`: Sanal kablo loglarını cihazda tutma seçeneği.
- `Paket Filtreleme Logları`: Paket filtreleme loglarını cihazda tutma seçeneği. (Seçili)
- `Durum`: DMZ sunucusunun durumu aktif olup olmadığını belirler.
- `DMZ Türü`: DMZ sunucusunun türü seçimi yapar.
- `Adres Ailesi`: IPv4 veya IPv6 adres ailesini seçer.
- `DMZ IP Arayüzü`: DMZ sunucusunun IP arayüzünü seçer.
- `DMZ IP Adresi`: IPv4 veya IPv6 adres ailesini seçer ve DMZ sunucusunun IP adresini girer.
- `Loglama`: DMZ sunucusunun loglama durumu aktif olup olmadığını belirler.
- `Erişim Denetimi`: Erişim denetimini yönetmek için kullanılacak kuralı seçer.
- `Loglama`: Güvenlik kurallarında log tutulması istenilen kuralda etkinleştirilir.

## Uyarılar

- En üstteki satır en son gelen çıktıdır. Çıkış geçmişinde maksimum 100 satır gösterilir.
- Açıklama alanının konumu belirtilmediği için bilgi eksikliği varsa, bu field boş bırakılmalıdır.
- Açıklama alanının konumu belirtilmediği için bilgi eksikliği varsa, bu field boş bırakılmalıdır.
- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: Paket Filtreleme Logları

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/anlik-gozlem/anlik-log-monitoru/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
