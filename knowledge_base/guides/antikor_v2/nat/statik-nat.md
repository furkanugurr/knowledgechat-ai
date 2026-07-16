# Statik NAT

## Kapsam

Herhangi bir istemci için bir gerçek IP adresi ile eşleştirilmesidir. Eşleştirilecek istemci IP adresinin özel bir IP adresi olması gerekmektedir. Statik NAT yapılabilecek IP adres aralıkları aşağıda belirtilmiştir.

## Menü yolu

- `Statik NAT`
- `Erişimler > FTP Sunucu`
- `Erişimler > Ekle`

## Kullanım adımları

1. Durumu seçmek için '# Durum' seçeneğini kullanın.
2. Yerel IP arayüzünü girin.
3. Yerel IP adresini girin.
4. NAT arayüzünü girin.
5. NAT IP adresini girin.
6. Açıklamayı girin.
7. Alias IP atamasını girin.
8. Durum seçeneğini aktif hale getirin.
9. Adres Ailesi seçeneğini IPv4 olarak ayarlayın.
10. FTP sunucusunu düzenlemek için Ekle butonuna tıklanır.
11. Durum seçeneğini aktif hale getirin veya bırakın.
12. Servisleri seçin veya kaldırın.
13. Trafiği Logla seçeneğini açın veya kapatin.
14. Erişecek Ağ alanına IP adresi girin.

## Alanlar

- `# Durum` (Statik NAT paneli): Durumu seçmek için
- `Yerel IP Arayüzü` (Statik NAT paneli): Yerel IP arayüzünü girin
- `Yerel IP Adresi` (Statik NAT paneli): Yerel IP adresini girin
- `NAT Arayüzü` (Statik NAT paneli): NAT arayüzünü girin
- `NAT IP Adresi` (Statik NAT paneli): NAT IP adresini girin
- `Açıklama` (Statik NAT paneli): Açıklamayı girin
- `Alias IP Atama` (Statik NAT paneli): Alias IP atamasını girin
- `Göster/Gizle` (Sayfa Başı Kayıt Sayısı): Tabloyu göster veya gizleme seçenekleri.
- `Sayfa Başı Kayıt Sayısı` (Sayfa Başı Kayıt Sayısı): Sayfada görüntülenecek kayıtların sayısı.
- `Tamam` (Sayfa Başı Kayıt Sayısı): Tüm verileri gösterme seçenekleri.
- `Filtrele` (Sayfa Başı Kayıt Sayısı): Tabloyu filtreleme seçenekleri.
- `Filtreyi Temizle` (Sayfa Başı Kayıt Sayısı): Filtreleri temizleme seçenekleri.
- `Erişecek Ağ` (Erişimler paneli): Erişilecek ağın IP adresini girer.

## Görünür kontroller

- `Yenile`: Listeyi yeniden yükleme
- `+ Ekle`: Yeni bir statik NAT kaydı ekleme
- `Göster/Gizle`: Liste gösterimini gizleme veya gösterme
- `Filtrele`: Listeyi filtreleme
- `Filtreyi Temizle`: Filtreleri temizleme
- `Durum`: Statik NAT işleminin aktif olup olmadığını belirler.
- `Adres Ailesi`: IP adresinin ailesini seçer. Seçenekler: IPv4, IPv6
- `Geri Dön`: Arka sayfaya dön.
- `Ekle`: FTP sunucusunu eklemek için.
- `Servisler`: Erişilecek hizmetleri seçer.
- `Trafiği Logla`: Statik NAT erişimlerinin trafiğini loglayıp loglamayacağını belirler.

## Uyarılar

- Bu tabloda yazdığınız portlar dışındaki bütün portlar erişime kapatılacaktır. Hiçbir port erişimi yazmamanız durumunda, bütün portlara dışardan erişilebilecektir.
- Açıklama alanını doldurun veya boş bırakın.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/nat-yapilandirmasi/statik-nat/
- Güven puanı: 1.00
