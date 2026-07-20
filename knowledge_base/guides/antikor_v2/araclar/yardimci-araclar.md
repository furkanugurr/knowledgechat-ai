# Yardımcı Araçlar

## Kapsam

İster yerel ağdan ister internetten bir IP’ye ping atılabilir. Eğer ICMP yasağı yoksa, bu IP adresinden yanıt dönecektir. Bu sayede o IP adresine sahip cihazın açık olup olmadığı anlaşılabilir.

## Menü yolu

- `Yardımcı Araçlar > Ping`
- `Trace Route`

## Kullanım adımları

1. IPv4, IPv6 veya Alan Adı giriniz: 1.1.1.1
2. Boyut(Byte): 64 bytes
3. Kaynak Adres: (not specified)
4. Ping servisi başlatıldı.
5. IPv4, IPv6 veya Alan Adı giriniz alanına IP adresi veya alan adını girin.
6. Başlat butonuna tıklayın.
7. Türü menüsünü kullanarak DNS sorgulama türünü seçin.
8. IPv4, IPv6 veya Alan Adı alanına IP adresi veya alan adını girin.
9. Sunucu Adresi alanına IP adresini girin.
10. Başlat düğmesine tıklayarak DNS sorgulamasını başlatın.
11. Türü seçeneğini A olarak ayarlayın.
12. IPv4, IPv6 veya Alan Adı alanına 'turkiye.gov.tr' yazın.
13. Sunucu Adresi alanına '8.8.8.8' yazın.
14. Başlat düğmesine tıklayın.

## Alanlar

- `IPv4, IPv6 veya Alan Adı giriniz` (IPv4, IPv6 veya Alan Adı giriniz): Ping atılacak IP adresi veya alan adı girilir.
- `Boyut(Byte)` (Boyut(Byte)): Ping atılan veri boyutu girilir.
- `Kaynak Adres` (Kaynak Adres): Ping atılacak kaynak IP adresi girilir.
- `IPv4, IPv6 veya Alan Adı` (DNS Sorgulama): DNS sorgulamasını yapmak için IP adresi veya alan adı girilmesini gerektiren alan. Seçim seçenekleri A, AG, NS, MX, TXT, LOC, PTR, SRV, SOA, ALL, ANY, AAAA, CNAME ve HINFO'dur.
- `Sunucu Adresi` (DNS Sorgulama): DNS sorgulamasını yapmak için IP adresi girilmesini gerektiren alan. Seçim seçenekleri A, AG, NS, MX, TXT, LOC, PTR, SRV, SOA, ALL, ANY, AAAA, CNAME ve HINFO'dur.
- `Türü` (Yardımcı Araçlar paneli): DNS sorgusu tipini seçer. Seçenekler: A, MX, NS.

## Görünür kontroller

- `Ping`: Ping tabını seçerek IP adresine ping atmayı başlatır.
- `Trace Route`: Trace Route tabını seçerek belirtilen bir hedef IP adresine erişim için internet üzerinde hangi yönlendiricilerden geçtiğini gösterir.
- `DNS Sorgulama`: DNS Sorgulama tabını seçerek belirtilen bir hedef IP adresinin DNS adını sorgular.
- `Başlat`: Başlat butonu, Trace Route işlemini başlatır.
- `Temizle`: Temizle butonu, girdi alanlarını temizler.
- `Türü`: DNS sorgulama türünü seçmek için kullanılan menü. Seçim seçenekleri A, AG, NS, MX, TXT, LOC, PTR, SRV, SOA, ALL, ANY, AAAA, CNAME ve HINFO'dur.

## Uyarılar

- En üsteki kayıt en son gelen çıktıdır. Çıkış geçmişinde maksimum 25 satır gösterilir.
- En üsteki kayıt en son gelen çıktıdır. Çıktı geçmişinde maksimum 25 satır gösterilir.
- DNS sorgusu başlatıldı ve sonuçlar alındı.
- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: IPv4, IPv6 veya Alan Adı, Sunucu Adresi

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/araclar/yardimci-araclar/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
