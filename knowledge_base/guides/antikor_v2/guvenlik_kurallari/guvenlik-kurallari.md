# Güvenlik Kuralları

## Menü yolu

- `Genel Kurallar`
- `IP Kuralları > Ağ Tanımları`
- `IP Kuralları > Kaynak Güvenlik Bölgesi`
- `Hedef Adres > Servisler > IPv4`
- `IPv4 - Kayıt Ekleme Formu`

## Kullanım adımları

1. Grupu seçin ve kaydetmek için Kaydet butonuna tıklayın.
2. Kaynak Güvenlik Bölgesi menüsünden bir güvenlik bölge seçin.
3. Hedef Güvenlik Bölgesi menüsünden bir güvenlik bölge seçin.
4. Servisler menüsünden bir hizmet seçin.
5. Kaynak Adres alanına IP adresini girin veya listedeki IP'leri seçin.
6. Hedef Adres alanına IP adresini girin veya listedeki IP'leri seçin.
7. Zaman Dilimleri alanında uygun zaman dilimi seçin.
8. IPv4 butonuna tıklayın.

## Alanlar

- `Sıra No` (Genel Kurallar): Sequence number of the rule.
- `Durum` (Genel Kurallar): Status selection for the rule.
- `İşlem` (Genel Kurallar): Action selection for the rule.
- `Loglama` (Genel Kurallar): Logging status of the rule.
- `Ağ Geçidi` (Genel Kurallar): Network interface selection for the rule.
- `Açıklama` (Genel Kurallar): Description of the rule.
- `İnceleme Yöntemi` (Genel Kurallar): Inspection method status for the rule.
- `Kaynak Adres` (IP Kuralları panelinde 'Kaynak Adres' altındaki alan.): Kaynak adresini girerek IP kurallarını ayarlamak için kullanılan alan.
- `Hedef Adres` (IP Kuralları panelinde 'Hedef Adres' altındaki alan.): Hedef adresini girerek IP kurallarını ayarlamak için kullanılan alan.
- `Zaman Dilimleri` (IP Kuralları panelinde 'Zaman Dilimleri' altındaki alan.): Zaman dilimlerini seçmek için kullanılan alan.
- `IPv4` (IPv4): IPv4 adreslerini girin veya seçin.
- `IPv4 Aralığı` (IPv4 Aralığı): IPv4 aralıklarını girin veya seçin.
- `IPv6` (IPv6): IPv6 adreslerini girin veya seçin.
- `IPv6 Aralığı` (IPv6 Aralığı): IPv6 aralıklarını girin veya seçin.
- `FQDN` (FQDN): Fully Qualified Domain Name (FQDN) adreslerini girin veya seçin.
- `Harici` (Harici): Harici ağ tanımlarını girin veya seçin.
- `Gruplar` (Gruplar): Ağ gruplarını girin veya seçin.
- `NAT Havuzu` (NAT Havuzu): LAN2 çıkış (192.168.168.68) seçeneği aktif durumda.
- `Adı` (IPv4 - Kayıt Ekleme Formu): Adı
- `IP Adresi` (IPv4 - Kayıt Ekleme Formu): IP Adresi '200.100.10.0/24'
- `Açıklama` (IPv4 - Kayıt Ekleme Formu): Açıklama

## Görünür kontroller

- `Kaynak Güvenlik Bölgesi`: Ağın güvenli bölgelerini seçmek için kullanılan menü.
- `Hedef Güvenlik Bölgesi`: Ağın hedef güvenli bölgelerini seçmek için kullanılan menü.
- `Servisler`: Kullanılan hizmetleri seçmek için kullanılan menü.
- `Kaynak Güvenlik Bölgesi`: Ağın güvenli bölgelerini seçmek için kullanılan menü.
- `Hedef Güvenlik Bölgesi`: Ağın hedef güvenli bölgelerini seçmek için kullanılan menü.
- `Ekle`: Ağ tanımlarını eklemek için kullanılır.
- `İptal`: İptal butonu.
- `Kaydet`: Kaydet butonu.
- `Kapalı`: NAT yapılandırması kapalı durumunda.
- `Çıkış Adresi`: NAT çıkış adresini ayarlamak için kullanılan sekme.
- `Global NAT`: Global NAT yapılandırmasını ayarlamak için kullanılan sekme.

## Uyarılar

- Ağ tanımlarını kullanırken, hızlı ağ tanımları ekleme butonunu kullanarak ağ tanımlarını doğrudan IP kurallarına ekleyebilirsiniz. Bu, güvenlik kurallarında kullanılabilir.
- NAT yapılandırması kapalı durumunda.
- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: IPv4
- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: NAT Havuzu

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/guvenlik-ayarlari/guvenlik-kurallari/
- Güven puanı: 0.94
