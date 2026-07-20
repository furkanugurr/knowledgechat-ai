# Kural Tabanlı Yönlendirme (PBR)

## Kapsam

Kural Tabanlı Yönlendirme (PBR), veri paketlerini belirli kurallar veya filtreler doğrultusunda yönlendiren bir tekniktir. Bu yönlendirme yöntemi, kaynak ve hedef IP adresleri, bağlantı noktaları, trafik türleri, servisler, erişim listeleri, paket boyutları gibi çeşitli parametreler üzerinden uygulanabilir ve paketleri kullanıcı tanımlı yollara yönlendirebilir.

## Menü yolu

- `Örnek Yeni Kayıt > Seçilebilir Servisler`

## Kullanım adımları

1. Durum: Aktif
2. Ağ Geçidi: 192.168.33.10
3. Kaynak Adres: ( Adet: 1 )
4. Hedef Adres: ( Adet: 1 )
5. Servisler: Tuzak Portları, UDP, TRACEROUTE, TIMESTAMP, TELNET, TCP, MYSQL, LDAP, SNMP, ESP
6. Network: LAN1
7. Açıklama: Kural Tabanlı Yönlendirme(PBR)
8. İşlemler: Düzenle, Sil
9. Durum kutusunu seçmek için checkbox'ı işaretleyin.
10. IPv4 veya IPv6 adres ailesini seçmek için ilgili butonu tıklayın.
11. Ağ geçidini girin (IPv4 için gereklidir).
12. Kaynak adresi girin.
13. Hedef adresi girin.
14. Servisleri seçin. (Tümü, + butonu ile eklenir.)
15. Açıklama alanına gerekli bilgileri girin.
16. Seçilebilir Servisler menüsünü kullanarak, kural tabanlı yönlendirme uygulamasında kullanılacak olan seçilebilir servisleri belirleyin.
17. Kullanıcı, yukarıdaki listede verilen alanlardan bir veya birden fazla servisi seçerek, özelleştirilmiş yönlendirme kurallarını tanımlayabilir.

## Alanlar

- `Durum` (Durum): Kuralın durumu.
- `Ağ Geçidi` (Ağ Geçidi): Ağ geçidinin IP adresi.
- `Kaynak Adres` (Kaynak Adres): Kaynak IP adresi.
- `Hedef Adres` (Hedef Adres): Hedef IP adresi.
- `Servisler` (Servisler): Kullanılacak servisler.
- `Network` (Network): Ağ bilgisi.
- `Açıklama` (Açıklama): Kurala ait açıklama.
- `Adres Ailesi` (Adres Ailesi): Adres Ailesi
- `Listedekiler Hariç` (Kaynak Adres): Listedekiler Hariç

## Görünür kontroller

- `Yenile`: Ekrandaki verileri yeniden yükleme.
- `+ Ekle`: Yeni bir kural ekleme.
- `Göster/Gizle`: Ekrandaki verileri göster veya gizleme.
- `Sayfa Başı Kayıt Sayısı`: Verilerin sayfasına göre gösterilecek kayıtların sayısı.
- `Tamam`: Ekrandaki işlemleri tamamlama.
- `Filtrele`: Verileri filtreleme.
- `Filtreyi Temizle`: Filtreleri temizleme.
- `Durum`: Kuralın aktif olup olmadığını belirler.
- `IPv4`: Adres ailesini IPv4 olarak seçer.
- `IPv6`: Adres ailesini IPv6 olarak seçer.
- `Servisler`: Kural tabanlı yönlendirme uygulamalarında kullanılacak olan seçilebilir servisleri gösteren menü.

## Uyarılar

- Kaynak/hedef adres ve servis bilgilerine göre paketleri istenilen router'a yönlendirir.
- Seçilebilir Servisler seçeneği var ancak ekran görüntüsünde gösterilmiyor.
- The field names for 'Durum', 'Listedekiler Hariç' under 'Kaynak Adres' and 'Hedef Adres' are inferred from the context. These should be explicitly provided in the HTML context.
- The field name for 'Adres Ailesi' is not explicitly provided, but it's a radio button selection between IPv4 and IPv6.
- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: Adres Ailesi, Ağ Geçidi, Durum, Hedef Adres, Kaynak Adres, Listedekiler Hariç, Network, Servisler

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/yonlendirme-yonetimi/kural-tabanli-yonlendirme/
- Güven puanı: 0.94
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
