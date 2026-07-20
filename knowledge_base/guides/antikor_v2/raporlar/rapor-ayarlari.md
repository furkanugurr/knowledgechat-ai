# Log Arşiv Yapılandırması

## Kapsam

title: log arsiv yapilandirmasi —

## Menü yolu

- `Log Arşiv Yapılandırması > Web Erişim Raporları`

## Kullanım adımları

1. Logların imzalanması(Kamu SM Zamane veya Antikor Zaman Damgası) ve farklı bir sunucuya FTP, SAMBA, NFS, SFTP, SCP dosya paylaşım türlerinden herhangi biri ile yedeklenmesi rapor ayarlarında yapılmaktadır.
2. Not: Disk boyutuna göre imzalı logların Arşivlenmiş Log Saklama Süresi ve Sorgulanabilir Log Saklama Süresi seçilmelidir.
3. KVKK uyarısını okuyun.
4. KVKK uyarısını onaylamak için 'Evet' butonuna tıklayın.
5. Log İmzalama seçeneğini aktif hale getirin.
6. Parolayı girin.
7. Sunucu tipini seçin.
8. Log imzalama algoritmasını seçin.
9. Sunucuya yedekleme seçeneğini aktif hale getirin.
10. Dosya paylaşım türünü seçin.
11. Adres ailesini seçin.
12. Sunucunun IP adresini girin.
13. Sunucunun port numarasını girin.
14. Sunucuya bağlanmak için kullanıcı adı girin.
15. Sunucuya bağlanmak için parolayı girin.

## Alanlar

- `İmza Programı` (Log İmzalama): Logların imzalanması için kullanılan imza programı (Kamu SM Zamane veya Antikor Zaman Damgası)
- `Müşteri No` (Log İmzalama): Rapor ayarlarında müşteri numarası
- `Parola` (Sunucu Yedekleme): Sunucuya yedekleme için gerekli parola
- `Algoritma` (Log İmzalama): Log imzalama algoritması (SHA 256 veya SHA 512)
- `Arşivlenmiş Log Saklama Süresi` (Log İmzalama): Arşivlenmiş logların saklama süresi (yıllar)
- `Sorgulanabilir Log Saklama Süresi` (Log İmzalama): Sorgulanabilir logların saklama süresi (aylar)
- `Dosya Paylaşım Türü` (Sunucu Yedekleme): Sunucuya yedeklenen dosya paylaşım türü (FTP, SAMBA, NFS, SFTP, SCP)
- `Adres Ailesi` (Sunucu Yedekleme): Sunucuya yedeklenen dosya adres ailesi (IPv4 veya IPv6)
- `Sunucu Adresi` (Sunucu Yedekleme): Sunucunun IP adresi
- `Sunucu Portu` (Sunucu Yedekleme): Sunucunun port numarası
- `Kullanıcı Adı` (Sunucu Yedekleme): Sunucuya FTP, SAMBA, NFS, SFTP, SCP ile dosya göndermek için gerekli kullanıcı adı
- `Hedef Klasör` (Sunucu Yedekleme): Sunucuya FTP, SAMBA, NFS, SFTP, SCP ile dosya göndermek için gerekli hedef klasör
- `Log İmzalama` (Log İmzalama): Log imzalama programı seçimi.
- `Sunucu` (Sunucu): Sunucu tipi seçimi.
- `Sunucuya Yedekleme` (Sunucuya Yedekleme): Sunucuya yedekleme seçimi.

## Görünür kontroller

- `Log Çeşidi`: Web Erişim Raporları (Http / Https / Proxy) seçeneğini gösteren bir menü.
- `İç IP Adresini İstek Başlıklarına Dahil Et`: Logların iç IP adresini istek başlıklarına dahil etme seçeneği
- `Log İmzalama`: Logların imzalanması için kullanılan imza programı seçimi
- `İptal`: Bu butona tıkladığınızda işlem iptal edilir.
- `Evet`: Bu butona tıkladığınızda KVKK uyarısını onaylar ve sunucuya yedekleme özelliğini aktif eder.
- `Aktif`: Log Arşivi yapılandırmasını aktive etme.

## Uyarılar

- Sunucuya yedekleme özelliği aktive edilince aşağıdaki KVKK uyarısı ile karşılaşılmaktadır.
- Yukarıdaki uyarıyı okuyup onayladığınız takdirde sunucu bilgilerinizi girip, loglar o sunucuya FTP, SAMBA, NFS, SFTP, SCP ile gönderilebilmektedir.
- Bu ayarı aktifleştirdiğinizde erişim kayıtları içerisinde yer alan kişisel veriler de ürün dışarısına transfer edilebilecektir. KVKK gereği bu işleme onayınız gerekmektedir.
- Sunucuya yedekleme özelliği aktive edilince aşağıdaki KVKK uyarısı ile karşılaşılmaktadır. Yükseltilen uyarı okuyup onayladığınız takdirde sunucu bilgilerinizi girip, loglar o sunucuya FTP, SAMBA, NFS, SFTP, SCP ile gönderilebilmektedir.
- Sunucunun IP adresi ve port numarası bilgilerinin doğru olup olmadığını kontrol edin.
- Sunucuya bağlanmak için kullanıcı adı ve parola bilgilerinin doğru olup olmadığını kontrol edin.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/raporlar/rapor-ayarlari/
- Güven puanı: 0.82
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
