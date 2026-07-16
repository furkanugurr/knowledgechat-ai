# L2TP/PPTP VPN Ayarları

## Kapsam

L2TP (Layer 2 Tunneling Protocol): L2TP, sanal özel ağlar (VPN) oluşturmak için kullanılan bir protokoldür. Genellikle IPsec ile birlikte kullanılır ve güvenli iletişim sağlamak amacıyla kullanıcıların uzak bir ağa erişmelerini sağlar.

## Kullanım adımları

1. Çalışma modunu seçin: PPTP ve L2TP, Sadece L2TP veya Sadece PPTP
2. IPsec şifreleme özelliğini etkinleştirin veya devre dışı bırakın.
3. Ön paylaşım anahtarını girin (isteğe bağlı).
4. Kişi başına oturum açma limitini belirleyin (isteğe bağlı).
5. Başlangıç IP adresini girin.
6. Bitiş IP adresini girin.
7. Sunucu IP adresini girin.
8. DNS sunucusu IP adresini girin.

## Alanlar

- `Ön Paylaşım Anahtarı` (Ön Paylaşım Anahtarı): Ön paylaşım anahtarının değeri. Eğer boş bırakılırsa varsayılan değer kullanılacaktır.
- `Kişi Başı Oturum Açma Limiti` (Kişi Başı Oturum Açma Limiti): Kişi başına oturum açma limitini belirler. Eğer boş bırakılırsa varsayılan değer kullanılacaktır.
- `Başlangıç IP` (Başlangıç IP): VPN bağlantısının başlangıç IP adresini belirler. Eğer boş bırakılırsa varsayılan değer kullanılacaktır.
- `Bitiş IP` (Bitiş IP): VPN bağlantısının bitiş IP adresini belirler. Eğer boş bırakılırsa varsayılan değer kullanılacaktır.
- `Sunucu IP` (Sunucu IP): VPN sunucusunun IP adresini belirler. Eğer boş bırakılırsa varsayılan değer kullanılacaktır.
- `DNS Sunucusu` (DNS Sunucusu): DNS sunucusunun IP adresini belirler. Eğer boş bırakılırsa varsayılan değer kullanılacaktır.

## Görünür kontroller

- `Çalışma Modu`: L2TP ve PPTP protokollerinin bir kombinasyonu, sadece L2TP veya sadece PPTP modlarını seçer.
- `IPsec Şifreleme`: IPsec şifrelemesinin aktif olup olmadığını belirler.

## Uyarılar

- L2TP ve PPTP servisleri, varsayılan ağ geçidi üzerinden bağlantı kurulmalıdır. Aksi halde bağlantı sorunu yaşanabilir.
- Bazı servis sağlayıcılar GRE paketlerini geçirmeyebilir. Bu nedenle L2TP over IPsec kullanılması gerekebilir; bu yapı GRE trafiğini şifreleyerek taşıyabilir ve bağlantı sorunlarını çözebilir.
- Ön paylaşım anahtarının değeri boş bırakıldığında varsayılan değer kullanılır.
- Kişi başına oturum açma limiti boş bırakıldığında varsayılan değer kullanılır.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/vpn-yonetimi/l2tp-pptp-vpn-ayarlari/
- Güven puanı: 1.00
