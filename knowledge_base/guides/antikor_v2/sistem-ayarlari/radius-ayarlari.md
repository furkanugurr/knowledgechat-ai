# RADIUS Ayarları

## Kapsam

RADIUS (Remote Authentication Dial In User Service) ağlara erişim sağlayan kullanıcıların AAA (Authentication, Authorization, Accounting) yani kimlik denetimi, yetkilendirme ve kayıt altına alma işlemleri yapabilmesi üzere oluşturulmuş bir protokoldür.

## Menü yolu

- `RADIUS Ayarları > RADIUS Profilleri`
- `RADIUS Ayarları > NAS Tanımları`
- `Sistem Ayarları > RADIUS Ayarları > NAS Tanımları`
- `Sistem Ayarları > Radius Ayarları`
- `RADIUS Ayarları > Proxy Etki Alanları`

## Kullanım adımları

1. RADIUS Ayarları sayfasına gidin.
2. RADIUS Profilleri sekmesini seçin.
3. Profil Adı alanına yeni profilin adını girin.
4. Kapsülleme seçeneğini PAP olarak belirleyin.
5. Operator Etki Alanı ve Açıklama alanlarını gerekli bilgilerle doldurun.
6. Kaydet butonuna tıklayarak eylemi kaydedin.
7. NAS tanımlamalarını görüntülemek için NAS Tanımları sekmesini seçin.
8. Profil Adı seçeneğini kullanarak bir profil adı belirleyin.
9. NAS Adı alanına bir NAS cihaz adı girin.
10. Adres Ailesi seçeneğini IPv4 veya IPv6 olarak ayarlayın.
11. NAS Adresi alanına NAS cihazının IP adresini girin.
12. Radius Şifresi alanına Radius şifresini girin.
13. Açıklama alanına gerekli açıklamaları girin.
14. Radius proxy havuzu listesini görüntülemek için 'Göster/Gizle' menüsünü kullanın.
15. Radius proxy havuzu sayfasındaki kayıtların sayısını ayarlamak için 'Sayfa Başı Kayıt Sayısı' menüsünü kullanın.
16. Radius proxy havuzu listesini filtrelemek için 'Filtrele' düğmesini kullanın.
17. Radius proxy havuzu listesini temizlemek için 'Filtreyi Temizle' düğmesini kullanın.
18. Radius proxy havuzu detaylarını görüntülemek veya düzenlemek için 'Düzenle' düğmesini kullanın.
19. Radius proxy havuzu silmek için 'Sil' düğmesini kullanın.
20. Radius proxy havuzu sunucularını görüntülemek için 'Sunucular' düğmesini kullanın.
21. Havuz adını girin.
22. Havuz tipini seçin (Fail Over).
23. Açıklamayı girin (isteğe bağlı).
24. Kaydet butonuna tıklayın.
25. Etki alanlarını düzenleyebilirsiniz.
26. Etki alanlarını silme işlemi yapabilirsiniz.
27. Proxy etki alanı adını girin.
28. Havuz seçeneğini belirleyin.
29. Etki alanına ait açıklama girin veya boş bırakın.
30. Kaydet düğmesine tıklayın.

## Alanlar

- `Durum` (RADIUS Profilleri panelinde): Profilin durumu (Aktif/Pasif).
- `Profil Adı` (RADIUS Profilleri panelinde): Profilin adı.
- `Kapsülleme` (RADIUS Profilleri panelinde): Kapsülleme metodu (PAP/EAP-TTLS/PAP).
- `RADIUS Proxy Kullan` (RADIUS Profilleri panelinde): RADIUS proxy kullanımları.
- `Operator Etki Alanı` (RADIUS Profilleri panelinde): Operatör etki alanı.
- `Açıklama` (RADIUS Profilleri panelinde): Profil açıklaması.
- `NAS Adı` (NAS Tanımları paneli): NAS tanımlamasının adı.
- `NAS Adresi` (NAS Tanımları paneli): NAS tanımlamasının IP adresi.
- `Adres Ailesi` (Adres Ailesi seçeneği): IPv4 or IPv6 address family selection.
- `Radius Şifresi` (Radius Tanımları paneli): Password for Radius authentication.
- `Göster/Gizle` (RADIUS Proxy Havuzları sekmesi altı): Liste gösterimini gizlemek veya gösterebilmek için kullanılan menü. Şu anda 'Göster' seçili durumda.
- `Sayfa Başı Kayıt Sayısı` (RADIUS Proxy Havuzları sekmesi altı): Liste sayfasındaki kayıtların sayısı ayarlamak için kullanılan menü. Şu anda 'Tamam' seçili durumda.
- `Filtrele` (RADIUS Proxy Havuzları sekmesi altı): Liste filtrelenmesini etkinleştirmek için kullanılan düğme. Şu anda etkin durumda.
- `Filtreyi Temizle` (RADIUS Proxy Havuzları sekmesi altı): Liste filtresini temizlemek için kullanılan düğme. Şu anda etkin durumda.
- `#` (RADIUS Proxy Havuzları sekmesi altı): Havuzun sıralama numarasını gösteren alan. Şu anda '1' değerinde.
- `Havuz Adı` (RADIUS Proxy Havuzları sekmesi altı): Radius proxy havuzu adını gösteren alan. Şu anda 'EDUROAM-FTLR' değerinde.
- `Havuz Tipi` (RADIUS Proxy Havuzları sekmesi altı): Radius proxy havuzu tipini gösteren alan. Şu anda 'Fail Over' değerinde.
- `işlemler` (RADIUS Proxy Havuzları sekmesi altı): Radius proxy havuzu ile ilgili işlemler için kullanılan alan. Şu anda 'Düzenle', 'Sil' ve 'Sunucular' seçenekleri mevcut.
- `Varsayılan RADIUS Proxy Havuzu` (RADIUS Ayarları paneli): Etkinlik listesinin ilk etki alanı adı
- `Etki Alanı Adı` (Proxy Etki Alanları paneli): Etkinlik listesinin ilk etki alanı adı
- `Havuz` (Havuz): Etki alanının havuzu seçmek için kullanılan etiket.

## Görünür kontroller

- `Yenile`: Ekrandaki verileri yeniden yükleme.
- `+ Ekle`: Yeni bir RADIUS profil eklemek için.
- `Göster/Gizle`: Veri gösterimini gizleme veya gösterme seçenekleri.
- `Tamam`: Seçilen filtreleri uygulama ve listeyi güncellemek için.
- `Filtrele`: Verileri filtrelemek için.
- `Filtreyi Temizle`: Filtreleri temizlemek ve listeyi genel olarak gösterecek.
- `Durum`: Aktif durumu belirtir.
- `İptal`: Eylem iptal etmek için kullanılır.
- `Kaydet`: Eylemi kaydetmek için kullanılır.
- `NAS Tanımları`: Radius ayarlarını yönetmek için kullanılan tab.
- `Ekle`: Yeni bir NAS tanımlaması eklemek için kullanılan düğme.
- `Düzenle`: Seçilen NAS tanımlamasını düzenlemek için kullanılan düğme.
- `Sil`: Seçilen NAS tanımlamasını silmek için kullanılan düğme.
- `RADIUS Profilleri`: Radius profillerini yönetmek için kullanılan sekme.
- `RADIUS Proxy Havuzları`: Radius proxy havuzlarını yönetmek için kullanılan sekme. Aktif olan ve failover tipiyle ayarlanmış bir havuzu listeler.
- `Proxy Etki Alanları`: Proxy etki alanlarını yönetmek için kullanılan sekme.
- `Sayfa Başı Kayıt Sayısı`: Sayfa başına kayıtların sayısı ayarlamak için
- `Türü`: Etki alanının türünü seçmek için kullanılan etiket.

## Uyarılar

- Bu formda kaydedilen bilgileri iptal etmek için 'İptal' butonuna tıklayın.
- Kaydedilen bilgileri kaydetmek için 'Kaydet' butonuna tıklayın.
- Doğrulama yaparken etki alanını çıkar seçeneği kullanılsınsa, etki alanı doğrulanırken kaldırılacaktır.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/sistem-ayarlari/radius-ayarlari/
- Güven puanı: 0.94
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
