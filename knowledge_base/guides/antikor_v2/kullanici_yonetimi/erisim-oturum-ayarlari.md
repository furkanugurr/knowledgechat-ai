# Erişim / Oturum Ayarları

## Kapsam

Bu sayfa, erişim ve oturum ayarlarını yapılandırmak için kullanılır. Kullanıcıların giriş yapmadan önce kabul etmeleri gereken şartları belirleyen bir feragatname içerir. Ayrıca SSH karşılama ekranı durumunu etkinleştirmek, eş zamanlı oturum sayısını ayarlamak ve TCP zaman aşımını belirtmek gibi çeşitli seçenekler sunar.

## Menü yolu

- `Giriş Feragatnamesi`
- `Oturum Ayarları`
- `Erişim / Oturum Ayarları > Erişebilen Ağlar - Yeni Kayıt`

## Kullanım adımları

1. Trafiği Logla seçeneğini etkinleştirmek için checkbox'u işaretleyin.
2. Sertifika Bazlı Kimlik Doğrulama seçeneğini etkinleştirmek için checkbox'u işaretleyin.
3. Harici Kaynaklardan Kimlik Doğrulama seçeneğini etkinleştirmek için checkbox'u işaretleyin.
4. Eş Zamanlı Oturum Sayısı değeri 100 olarak ayarlayın.
5. DOS Bağlantı Limitleme seçeneğini etkinleştirmek için checkbox'u işaretleyin.
6. QoS Hız Limitleme seçeneğini etkinleştirmek için checkbox'u işaretleyin.
7. TCP zaman aşımı değeri 3600 olarak ayarlayın.
8. Çalışma Modu'nu 'Kısıtlı Erişim' olarak ayarlayın.
9. Giriş Feragatnamesi seçeneğini etkinleştirmek için checkbox'u işaretleyin.
10. SSH Karşılama Ekran Durumu seçeneğini etkinleştirmek için checkbox'u işaretleyin.
11. Dikkat!!! Yetkilisi de olmayan kullanıcılar giriş denemesi yapmamalıdır. Dikkat!!!
12. IP adresi girin ve Düzenle butonuna tıklayın.

## Alanlar

- `Eş Zamanlı Oturum Sayısı` (Oturum Ayarları): Eş zamanlı oturum sayısını belirler.
- `TCP zaman aşımı (Saniye)` (Oturum Ayarları): TCP zaman aşımını belirler.
- `IP Adresi` (Erişebilen Ağlar panelinde): Erişebilen ağların IP adreslerini girme alanı.
- `#` (Erişebilen Ağlar panelinde): Seçenek sayısını gösteren alan.
- `Açıklama` (Yönetim Paneli Ayarları - Yeni Kayıt): IP adresine ait açıklama bilgisi girileceği alan.

## Görünür kontroller

- `Trafiği Logla`: Trafik kaydını etkinleştirir.
- `Sertifika Bazlı Kimlik Doğrulama`: Sertifika tabanlı kimlik doğrulamayı etkinleştirir.
- `Harici Kaynaklardan Kimlik Doğrulama`: Harici kaynaklardan kimlik doğrulamasını etkinleştirir.
- `DOS Bağlantı Limitleme`: DoS bağlantı sınırlamayı etkinleştirir.
- `QoS Hız Limitleme`: QoS hız sınırlamayı etkinleştirir.
- `Giriş Feragatnamesi`: Kullanıcıların giriş yapmadan önce kabul etmeleri gereken şartları belirleyen feragatnameyi etkinleştirir.
- `SSH Karşılama Ekran Durumu`: SSH karşılama ekran durumunu etkinleştirmek için kullanılır.
- `Onayla`: Giriş feragatnamesini kabul etmek için kullanılan buton.
- `İptal`: Feragatnameyi kabul etmeyi reddetmek için kullanılan buton.
- `Kaydet`: Yapılan değişiklikleri kaydetmek için kullanılır.
- `Yenile`: Erişebilen ağ listesini yeniden yükleme.
- `+ Ekle`: Yeni bir IP adresi eklemek için kullanılır.
- `Düzenle`: Seçilen IP adresinin bilgilerini düzenlemek için kullanılır.
- `Sil`: Seçilen IP adresini silmek için kullanılır.
- `İptal`: Kaydedilmeyen yeni kaydı iptal etmek için kullanılan düğme.

## Uyarılar

- Trafiği Logla, Sertifika Bazlı Kimlik Doğrulama ve Harici Kaynaklardan Kimlik Doğrulama seçeneklerini etkinleştirdiğinizde, güvenlik ayarlarını dikkatli bir şekilde yönetmelisiniz.
- Yapılan tüm işlem ve denemeler kayıtlara alınmaktadır. Parola zorlaması vb. her türlü giriş hakkındaki yasal işlem başlatılacaktır.
- DİKKAT!!! YETKİLİ DEĞİLSENİZ GİRİŞ DENEMESİ YAPMAYINIZ!! Yapılan tüm işlem ve denemeler kayıt altına alınmaktadır. Parola zorlaması vb. her türlü girişim hakkında yasal işlem başlatılacaktır.
- Eş Zamanlı Oturum Sayısı, DOS Bağlantı Limitleme, QoS Hız Limitleme ve TCP zaman aşımı değerlerini ayarlamak için gerekli olan metin kutusu bulunmamaktadır.
- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: Eş Zamanlı Oturum Sayısı, TCP zaman aşımı (Saniye)
- SSH parola girişinin tamamlandığı konusunda belirtilen IP adresi bilgisi yoktur.
- Kullanıcı adı ve şifre bilgilerinin gizliliği konusunda daha fazla bilgi sağlanmamıştır.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/kullanici-yonetimi/erisim-oturum-ayarlari/
- Güven puanı: 0.94
