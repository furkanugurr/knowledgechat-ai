# SSL VPN Ayarları

## Kapsam

SSL VPN (Secure Sockets Layer Virtual Private Network - Güvenli Yuva Katmanı Tabanlı Sanal Özel Ağ): uzaktan erişim için kullanılan ve SSL sertifikalarıyla şifrelenmiş güvenli bir iletişim sağlayan sanal özel ağ türüdür. IPSec VPN’in bazı zorlukları nedeniyle tercih edilen SSL VPN, WAN IP adresi belirleme, VPN ağı adresi tanımlama, DNS ayarları, protokol ve port numarası seçimi gibi ayarları içerir. Kullanıcı doğrulama seçenekleri arasında kullanıcı adı/parola veya sertifika doğrulaması gibi seçenekler bulunabilir. SSL VPN kullanıcıları için oturum açma limitleri belirlenebilir ve sertifika yönetimi de sağlanabilir.

## Menü yolu

- `Sertifika Yönetimi > Kullanıcıların VPN kayıtlarının yapıldığı ve işletim sistemine uygun konfigurasyon dosyasının indirildiği sayfadır.`

## Kullanım adımları

1. WAN IP adresini girin
2. DNS ayarlarını girin
3. Alan adı sunucusunu girin
4. Kimlik doğrulamasını seçin (SHA1)
5. Kriptolama algoritmasını seçin (AES-256-CBC)
6. Protokolü seçin (UDP)
7. Port numarasını girin (1194)
8. Erişilecek ağıları girin
9. Çalışma modunu seçin (Sertifika Doğrulama)
10. Kişi başı oturum açma seçeneğini girin (Antikor, Generic OpenVPN)
11. Kimlik Bilgileri: 111********11 - Antikor Admin
12. IP Adresi: 1.0.0.0
13. Erişilecek Ağlar: (Adet: 2) 0.0.0.0/0 ::/0
14. Açıklama: SSL VPN
15. İşlemler: Düzenle, Sil, İndir
16. Kullanıcı Adı alanına kullanıcı adınızı girin.
17. Rezerve IP Adresi alanına IPv4 adresini girin.
18. Erişilecek Ağlar alanına erişilecek ağları girin.
19. Açıklama alanına açıklama yapın.
20. Kaydet butonuna tıklayın.
21. Gösterim modunu değiştirin.
22. Kayıtları filtreleyin.
23. Filtreleri temizleyin.
24. İstenilen işletim sistemine uygun sertifika indirmesi yapmak için 'İndir' butonuna tıklayın.

## Alanlar

- `WAN IP Adresi` (Ayarlar paneli): WAN IP adresini girin
- `VPN Network Adresi` (Ayarlar paneli): VPN ağı adresini girin
- `DNS Ayarları` (Ayarlar paneli): DNS ayarlarını girin
- `Alan Adı Sunucusu` (Ayarlar paneli): Alan adı sunucusunu girin
- `Kimlik Doğrulama` (Ayarlar paneli): Kimlik doğrulamasını seçin (SHA1)
- `Kriptolama Algoritması` (Ayarlar paneli): Kriptolama algoritmasını seçin (AES-256-CBC)
- `Protokol` (Ayarlar paneli): Protokolü seçin (UDP)
- `Port Numarası` (Ayarlar paneli): Port numarasını girin (1194)
- `Erişilecek Ağılar` (Ayarlar paneli): Erişilecek ağıları girin
- `Çalışma Modu` (Ayarlar paneli): Çalışma modunu seçin (Sertifika Doğrulama)
- `Kişi Başı Oturum Açma` (Ayarlar paneli): Kişi başı oturum açma seçeneğini girin (Antikor, Generic OpenVPN)
- `Sayfa Başı Kayıt Sayısı` (Sertifika Yönetimi paneli): Sayfanın içeriğini göstermek istediğiniz kayıtların sayısı.
- `Kullanıcı Adı` (Kullanıcı Ayar Atama paneli): Kullanıcı adını girin.
- `Rezerve IP Adresi` (Rezerve IP Adresi alanı): IPv4 adresini girin.
- `Erişilecek Ağlar` (Erişilecek Ağlar alanı): Erişilecek ağları girin.
- `Açıklama` (Açıklama alanı): Açıklamayı girin.

## Görünür kontroller

- `Kaydet`: Ayarları kaydetmek için kullanılan düğme
- `Dahil Et`: DNS sunucusuna dahil etmek için kullanılan düğme
- `Yenile`: Sayfanın içeriğini yeniden yükleme.
- `Ekle`: Yeni bir SSL VPN ayarını eklemek için kullanılan düğme.
- `Göster/Gizle`: Sayfanın içeriğini göster veya gizleme seçenekleri.
- `Filtrele`: Arama ve filtreleme seçenekleri.
- `Filtreyi Temizle`: Filtrelerin temizlenmesi.
- `İptal`: Kapatma
- `İndir`: İstenilen işletim sistemine uygun sertifika indirmesi yapılır.

## Uyarılar

- Kimlik doğrulama aktif edilmesi halinde, Antikor’da kimlik doğrulama ayarlarının yapılması gerekmektedir.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/vpn-yonetimi/ssl-vpn-ayarlari/
- Güven puanı: 0.94
