# Kimlik Sağlayıcı Tanımları

## Kapsam

Bu doküman, kimlik sağlayıcısı tanımlarını oluşturmak ve yönetmek için kullanılan arayüzü detaylandırmaktadır. Farklı türde kimlik sağlayıcıları (POP3/IMAP, SMS, Yerel Gruplar, SSO) yapılandırılabilir.

## Menü yolu

- `Kimlik Sağlayıcı Tanımları`

## Kullanım adımları

1. Durum seçimi yapın (aktif/passif).
2. Sağlayıcı türü seçimi yapın ('POP3/IMAP', 'SMS', 'Yerel Gruplar' veya 'SSO: Negotiate/Kerberos - Active Directory').
3. Adı ve etki alanı birlikte kullanma seçeneğini işaretleyin (gerekirse).
4. Etki alanını seçin (örneğin, 'Kullanıcı ve Etki Alanı birlikte' veya boş bırakın).
5. Sunucu adresini girin (POP3/IMAP için).
6. Protokol seçimi yapın ('SSL' veya 'TLS', POP3/IMAP için).
7. Port numarasını girin (POP3/IMAP için).
8. Deneme sayısını seçin (POP3/IMAP için).
9. SMS ayarlarını, mesaj ön metnini ve açıklama alanlarını doldurun (SMS için).
10. Yetkili kullanıcıyı girin (Yerel Gruplar için).
11. KDC / DC DNS Adı ve Antikora atanan DNS Adı alanlarına gerekli bilgileri girin (SSO: Negotiate/Kerberos - Active Directory için).

## Alanlar

- `Adı` (Adı): Kimlik sağlayıcısının adını girme alanı. Adı ve etki alanı birlikte kullanılır.
- `Etki Alanı` (Etki Alanı): Etki alanını seçme seçenekleri. Seçenekler arasında 'Kullanıcı ve Etki Alanı birlikte' bulunur.  Bazı durumlarda boş bırakılabilir.
- `Sunucu Adresi` (Sunucu Adresi): Mail sunucusunun IP adresini girme alanı (POP3/IMAP için).
- `Protokol` (Protokol): Kimlik doğrulama için kullanılacak protokol seçimi. Seçenekler arasında 'SSL' ve 'TLS' bulunur (POP3/IMAP için).
- `Port` (Port): Mail sunucusunun port numarasını girme alanı (POP3/IMAP için).
- `Deneme Sayısı` (Deneme Sayısı): Kimlik doğrulama denemesi sayısı seçimi (POP3/IMAP için).
- `SMS Ayarları` (SMS Ayarları): SMS ayarlarını girin veya boş bırakın. SMS sağlayıcısı için özel ayarları içerir.
- `Mesaj Ön Metni` (Mesaj Ön Metni): SMS mesajının ön metnini girin veya boş bırakın.
- `Yetkili Kullanıcı` (Yetkili Kullanıcı): Kimlik sağlayıcısının yetkilisi olarak seçilen kullanıcıyı girin (Yerel Gruplar için).
- `KDC / DC DNS Adı` (KDC / DC DNS Adı): KDC (Key Distribution Center) veya Domain Controller (DC) DNS adını girilmesini sağlar (SSO: Negotiate/Kerberos - Active Directory için). Şu anda boş bırakılmıştır.
- `Antikora atanan DNS Adı` (Antikora atanan DNS Adı): Antikora atanan DNS adını girilmesini sağlar (SSO: Negotiate/Kerberos - Active Directory için). Şu anda boş bırakılmıştır.
- `Açıklama` (Açıklama): Kimlik sağlayıcısına ait açıklama alanı. Açıklamayı girme alanı veya sağlayıcının işlevini ve özelliklerini belirtmek için kullanılabilir.

## Görünür kontroller

- `Durum`: Kimlik sağlayıcısının durumu (aktif/passif) seçimi.
- `Sağlayıcı Türü`: Kimlik sağlayıcısı türü seçimi. Seçenekler arasında 'POP3/IMAP', 'SMS', 'Yerel Gruplar' ve 'SSO: Negotiate/Kerberos - Active Directory' bulunur.
- `Durum`: Kimlik sağlayıcısının aktif olup olmadığını belirler.
- `Sağlayıcı Türü`: Kimlik sağlayıcısı tipini seçmek için kullanılır.

## Uyarılar

- SMS
- Yerel Gruplar
- Domain Controller / Kerberos Key Distribution Center ile saat uyumu olmazsa Tek Oturum Açma (SSO) başarısız olabilir. Lütfen Tarih Saat Ayarları menüsünden NTP senkronizasyonu yapıldığından emin olun.
- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: Adı, Açıklama, Deneme Sayısı, Etki Alanı, Port, Protokol, Sunucu Adresi
- Etki alanı, KDC / DC DNS Adı ve Antikora atanan DNS Adı alanları boş bırakılmıştır. Bu alanlara gerekli bilgilerin girilmesi gerekebilir.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/kimlik-dogrulama-kurallari/kimlik-saglayici-tanimlari/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
