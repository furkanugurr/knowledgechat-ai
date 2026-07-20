# DHCP Ayarları

## Kapsam

DHCP (Dynamic Host Configuration Protocol) networkte ağa bağlanabilen cihazlara özel bir IP atama işlemi gerçekleştiren sunuculardır. Sistemde kullanılan DHCP ayarları buraya girilir. Kira süresi ve DHCP Opsiyonları bu bölümde oluşturulur. Ayrıca DHCP sunucusu için özel opsiyonlar da tanımlanabilir. Farklı vlanlara farklı DNS tanımlanabilir. VLAN bazlı opsiyonlara tanımların eklenmesi yeterli olacaktır.

## Menü yolu

- `DHCP Ayarları > Kullanıcı Tanımlı Opsiyonlar`
- `Kullanıcı Tanımlı Opsiyonlar > Kullanıcı Tanımlı Opsiyonlar Yeni Kayıt`
- `Kullanıcı Tanımlı Opsiyonlar > Genel Opsiyonlar > VLAN Opsiyonları`
- `Genel Opsiyonlar > Genel Opsiyonlar Yeni Kayıt`
- `Genel Opsiyonlar > VLAN Opsiyonları`
- `VLAN Opsiyonları > VLAN Opsiyonları Yeni Kayıt`
- `DHCP Ayarları > İstemci Opsiyonları`

## Kullanım adımları

1. DHCP ayarlarını görüntülemek için 'DHCP Ayarları' sayfasına gidin.
2. Yeni bir DHCP opsiyonu eklemek için 'Ekle' düğmesine tıklayın.
3. Opsiyonları düzenleme veya silme için 'Düzenle' ve 'Sil' butonlarını kullanın.
4. Opsiyon adını girin.
5. Kodu girin.
6. Veri tipini seçin.
7. Kaydedilen bilgileri kaydetmek için 'Kaydet' butonuna tıklayın.
8. Kira süresini seçin ve 'Kaydet' düğmesine tıklayın.
9. Durum seçeneğini aktif olarak belirleyin.
10. Opsiyon türünü seçin.
11. Değer alanına opsionun değerini girin.
12. Açıklama alanına opsion hakkında ek bilgi girin.
13. Kaydet butonuna basarak kaydedin.
14. Kısa menüdeki 'Genel Opsiyonlar' seçeneğini tıklayın.
15. Seçilen menüden 'VLAN Opsiyonları' seçeneğini tıklayın.
16. Opsiyon seçin.
17. Opsiyon tipini belirleyin.
18. Değeri seçin veya girin.
19. Network'i seçin.
20. Açıklamayı girin.
21. Kaydet butonuna tıklayın.
22. Kira süresini seçin ve kaydedin.
23. Durum seçeneğini aktif olarak işaretleyin veya bırakın.
24. Değer alanına opsiyon değerini girin.
25. İstemcileri seçin.
26. Açıklama alanına opsiyon açıklamasını girin.
27. Kaydet butonuna basarak opsiyonu kaydedin.

## Alanlar

- `Sayfa Başı Kayıt Sayısı` (Kullanıcı Tanımlı Opsiyonlar paneli): Sayfada gösterilecek kayıtların sayısı.
- `Sıra` (Kullanıcı Tanımlı Opsiyonlar): Opsiyonun sırasını belirler.
- `Opsiyon Adı` (Kullanıcı Tanımlı Opsiyonlar): Opsiyonun adını girer.
- `Kodu` (Kullanıcı Tanımlı Opsiyonlar): Opsiyonun kodunu girer.
- `Protokol` (Kullanıcı Tanımlı Opsiyonlar): Opsiyonun protokolünü belirler.
- `Veri Tipi` (Kullanıcı Tanımlı Opsiyonlar): Opsiyonun veri tipini belirler.
- `Açıklama` (Kullanıcı Tanımlı Opsiyonlar): Opsiyonun açıklamasını girer.
- `Kira Süresi` (Genel Opsiyonlar panelinde): DHCP kiralama süresini seçmek için kullanılan düşüm.
- `Opsiyon` (Genel Opsiyonlar - Yeni Kayıt paneli): Oluşturulan opsionun türünü seçer.
- `Değer` (Genel Opsiyonlar - Yeni Kayıt paneli): Opsiyonun değerini girer.
- `Network` (Network sütununda): Ağ adını girme alanıdır.
- `Durum` (Durum): Opsiyonun etkin olup olmadığını belirler.
- `Opsiyon Tipi` (Opsiyon Tipi): Opsiyonun tipini belirler.
- `İstemci` (İstemci Opsiyonları panelinde): İstemcinin durumunu belirtmek için.

## Görünür kontroller

- `Yenile`: Ekranı yeniden yükleme.
- `Ekle`: Yeni bir DHCP opsiyonu eklemek için kullanılan düğme.
- `Göster/Gizle`: Gösterilen verileri gizleme veya gösterme.
- `Filtrele`: Verileri filtrelemek için kullanılan düğme.
- `Filtreyi Temizle`: Filtreleri temizlemek için kullanılan düğme.
- `Sayfa Başı Kayıt Sayısı`: Veri sayfasındaki kayıtların sayısı ayarlama.
- `Tamam`: Ekrandaki değişiklikleri kaydetme.
- `İptal`: Kaydı iptal etmek için.
- `Kaydet`: Kaydedilen bilgileri kaydetmek için.
- `Durum`: Opsiyonun durumu aktif olup olmadığını belirler.

## Uyarılar

- Opsiyon türü 'Standart' seçildiğinde, opsionun değer ve açıklama alanları boş bırakılamaz.
- Opsiyon türünü ve istemciyi doğru olarak seçmek önemlidir. Yanlış seçimler veri eksikliği veya hataları neden olabilir.
- Ekranın üst kısmında 'Genel Opsiyonlar', 'VLAN Opsiyonları' ve 'İstemci Opsiyonları' gibi seçenekler var, ancak bu seçeneklerin etkinliği veya kullanımını gösteren bir kontrol yok.
- Opsiyonun kodu ve veri tipi hakkında daha fazla bilgi almak isterseniz, bu alanları doldurmanız gerekebilir.
- Opsiyon adı ve kodu boş bırakılamaz.
- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: Açıklama, Değer, Durum, Network, Opsiyon, Opsiyon Tipi

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/sistem-ayarlari/dhcp-ayarlari/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
