# Doğrulama Kuralları

## Kapsam

Doğrulama Kuralları’nın tanımlandığı bölümdür.

## Menü yolu

- `Doğrulama Kuralları > Hotspot`
- `Hotspot Giriş Ekranı > Proxy > Kayıt Servisi`
- `Hotspot Giriş Ekranı > Proxy`
- `Proxy > Kayıt Servisi`
- `Kayıt Servisi > L2TP / PPTP VPN`
- `L2TP VPN > SSL VPN`
- `SSL VPN > RADIUS`
- `RADIUS > İstemci Değişikliği Formu`
- `İstemci Değişikliği Formu > Yönetim Paneli`

## Kullanım adımları

1. Network alanını seçin ve hotspot uygulaması için kullanılacak ağları belirleyin.
2. Tek Oturum Açma SSO özelliğini etkinleştirmek isterseniz checkbox'ı işaretleyin.
3. Uyruk seçeneğini Türkiye olarak ayarlayın.
4. Kimlik numarası, ad ve soyad bilgilerini girmeniz gerekmektedir.
5. Proxy sayfasına geçmek için 'Proxy' menüsünü seçin.
6. Her Durumda Sistem Yöneticisi Onayı seçeneğini etkinleştirin veya devre dışı bırakın.
7. Sistem Yöneticisi Onayı ya da İstemci Onayı seçeneğini etkinleştirin veya devre dışı bırakın.
8. Mernis hizmet sağlayıcısını seçin.
9. SMS hizmet sağlayıcısını seçin.
10. Navigate to the RADIUS tab.
11. Enable Mernis authentication by checking the corresponding checkbox.

## Alanlar

- `Network` (Network): Hotspot uygulaması için kullanılacak ağları seçmek için kullanılan dropdown.
- `Tek Oturum Açma SSO` (Tek Oturum Açma SSO): Tek oturum açma SSO özelliğini etkinleştirmek için kullanılan checkbox.
- `Mernis` (Mernis): Mernis doğrulama kurallarını yönetmek için kullanılan text field.
- `SMS` (SMS): SMS doğrulama kurallarını yönetmek için kullanılan text field.
- `IP` (IP): IP doğrulama kurallarını yönetmek için kullanılan text field.
- `Sağlayıcılar` (Sağlayıcılar): Sağlayıcıları seçmek için kullanılan dropdown.
- `Kimlik Numarası` (Kimlik Numarası): Kimlik numarası girilecek alan
- `Adı` (Adı): Ad girilecek alan
- `Soyadı` (Soyadı): Soyadı girilecek alan
- `Doğum Tarihi` (Doğum Tarihi): Doğum tarihi girilecek alan
- `Etki Alanı` (SSL VPN tab): Etki Alanı
- `Kullanımında` (SSL VPN tab): Kullanımında
- `RADIUS Profili` (RADIUS tab): Dropdown menu for selecting a RADIUS profile. Currently, it shows 'Tek Bir Seçim Yapabilirsiniz...' which translates to 'You can make only one selection...'.

## Görünür kontroller

- `Hotspot`: Hotspot doğrulama kurallarını yöneten sekme.
- `Proxy`: Proxy doğrulama kurallarını yöneten sekme.
- `Kayıt Servisi`: Kayıt servisi doğrulama kurallarını yöneten sekme.
- `L2TP / PPTP VPN`: L2TP/PPTP VPN doğrulama kurallarını yöneten sekme.
- `SSL VPN`: SSL VPN doğrulama kurallarını yöneten sekme.
- `RADIUS`: RADIUS doğrulama kurallarını yöneten sekme.
- `İstemci Değişikliği Formu`: İstemci değişikliği formu doğrulama kurallarını yöneten sekme.
- `Yönetim Paneli`: Yönetim paneli doğrulama kurallarını yöneten sekme.
- `Uyruk`: Ülke seçimi
- `Kullanım koşullarını okudum ve kabul ediyorum.`: Kullanım koşullarına onay verme
- `Her Durumda Sistem Yöneticisi Onayı`: Enables system administrator approval in all situations.
- `Sistem Yöneticisi Onayı ya da İstemci Onayı`: Enables either system administrator or client approval.
- `Sağlayıcılar`: Dropdown menu to select service providers.
- `Seçiniz...`: Seçiniz...
- `Mernis`: Checkbox for enabling Mernis authentication method.
- `SMS`: Checkbox for enabling SMS authentication method.

## Uyarılar

- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: RADIUS Profili
- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: Etki Alanı, Sağlayıcılar

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/kimlik-dogrulama-kurallari/dogrulama-kurallari/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
