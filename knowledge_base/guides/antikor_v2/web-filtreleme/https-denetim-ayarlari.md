# HTTPS Denetim Ayarları

## Kapsam

HTTPS sayfaların filtrelenmesini sağlamaktadır.

## Menü yolu

- `Bağlantı Ayarları > HTTP İnceleme Ayarları, HTTPS İnceleme Ayarları`
- `TLS Ayarları > Kaynak Adrese Göre Çalışma Modu`
- `HTTPS Denetim Ayarları > Kaynak Adrese Göre Çalışma Modu > SNI Modunda Çalışacak Web Sayfaları`
- `WEB sayfasına ait sertifika ile açılması istenen WEB sayfaları bu sayfaya eklenmelidir.
SNI Modunda Çalışacak WEB Sayfaları HTTP(S) Denetim Ayarları - Yeni Kayıt
Sertifika Değiştirme Modunda Çalışacak WEB Sayfaları`
- `HTTP(S) Denetim Ayarları - Yeni Kayıt`

## Kullanım adımları

1. HTTP İnceleme Ayarları panelinde otomatik algılama durumunu kontrol edin ve gerekirse değiştirin.
2. HTTPS İnceleme Ayarları panelinde otomatik algılama durumunu kontrol edin ve gerekirse değiştirin.
3. TLS Ayarları panelinde zayıf SSL algoritmalarını engelle checkbox'ını kontrol edin ve gerekirse devre dışı bırakın.
4. TLS Ayarları panelinde SSLv3 desteğini engelle checkbox'ını kontrol edin ve gerekirse devre dışı bırakın.
5. Bağlantı Ayarları panelinde HTTPS denetim ayarlarını yönetmek için kullanın.
6. Kaynak Adresi girin.
7. HTTPS Denetim Modu seçeneğini belirleyin.
8. Web sayfasına ait sertifika ile açılması istenen WEB sayfaları bu sayfaya eklenmelidir.
9. Durum seçeneğini aktif hale getirin.
10. Alan Adı alanına WEB sayfanın alan adını girin.
11. Açıklama alanına eklemek istediğiniz açıklamayı girin.
12. Kaydet butonuna tıklayın.
13. WEB sayfasını eklemek için '+ Ekle' butonuna tıklayın.
14. Durumu aktif olarak işaretleyin.
15. Alan adını girin.

## Alanlar

- `Zayıf SSL Algoritmalarını Engelle` (TLS Ayarları): İstemci - Antikor arası ve Antikor - Sunucu arası TLS ayarlarında zayıf SSL algoritmalarını engellemek için kullanılan checkbox.
- `SSLv3 Desteği` (TLS Ayarları): İstemci - Antikor arası ve Antikor - Sunucu arası TLS ayarlarında SSLv3 desteğini engellemek için kullanılan checkbox.
- `SNI` (Bağlantı Ayarları): HTTPS denetim ayarlarında SNI modunu seçmek için kullanılan bir dropdown.
- `Durum` (Kaynak Adrese Göre Çalışma Modu): Kaynak adresine göre çalıştırılacak HTTPS denetim ayarlarını gösteren bir metin alan.
- `Kaynak Adres` (Kaynak Adrese Göre Çalışma Modu): HTTPS denetim ayarlarında kaynak adresini belirlemek için kullanılan bir metin alan.
- `HTTPS Denetim Modu` (Kaynak Adrese Göre Çalışma Modu): HTTPS denetim ayarlarında HTTPS denetim modunu belirlemek için kullanılan bir metin alan.
- `Açıklama` (Kaynak Adrese Göre Çalışma Modu): HTTPS denetim ayarlarında açıklamaları gösteren bir metin alan.
- `Göster/Gizle` (SNI Modunda Çalışacak Web Sayfaları): Listeyi göster veya gizlemek için kullanılır.
- `Sayfa Başı Kayıt Sayısı` (SNI Modunda Çalışacak Web Sayfaları): Sayfa başına kayıtların sayısı ayarlamak için kullanılır.
- `Alan Adı` (Durum altındaki alan): Eklenecek WEB sayfanın alan adını girin.
- `Filtrele` (Sertifika Değiştirme Modunda Çalışacak WEB Sayfaları): Listeye filtre uygulamak için kullanılır.
- `Filtreyi Temizle` (Sertifika Değiştirme Modunda Çalışacak WEB Sayfaları): Listeye filtre uygulamak için kullanılır.

## Görünür kontroller

- `Otomatik Algılama`: HTTP ve HTTPS inceleme ayarlarında otomatik algılama durumu.
- `Desteklenen Minimum TLS Sürümü`: TLS ayarlarında desteklenen minimum TLS sürümü seçeneği.
- `Varsayılan Mod`: HTTPS denetim ayarlarında kullanılan modu belirlemek için kullanılan bir dropdown.
- `Yenile`: Kayıtları yeniden yükleme için kullanılan bir düğme.
- `+ Ekle`: Yeni kayıtlar eklemek için kullanılan bir düğme.
- `Durum`: Ayarların aktif olup olmadığını belirler.
- `İptal`: Ekrandaki işlemleri iptal eder ve önceki sayfaya geri dönür.
- `Kaydet`: Ayarları kaydederek ekranda kalır.

## Uyarılar

- SNI olarak tanımlanan etki alanlarının SSL Serifikası değiştirilmeden orijinal sertifika ile iletişim kurulur. Bu nedenle ilgili etki alanlarında SSL trafiği deşifre edilemez ve derinlemesine inceleme yapılamaz.
- HTTPS herhangi bir adres engellendiğinde HTTP(S) Denetim Ayarlarında Kaynak Adrese Göre Çalışma Modu: SNI seçiliyse sayfa yasaklama ekranı gelmeyecek ama kullanıcının sayfaya erişimi yine de engellenecektir. SNI modda engellenen HTTPS sayfalarda, yasak uyarı sayfasının gelmeme nedeni sertifikanın araya girmemesi ve bundan dolayı sayfa yasaklama sayfasına yönlendirme yapılmasının mümkün olmamıştır.
- SNI modda engellenen HTTPS sayfalarda, yasak uyarı sayfasının gelmeme nedeni sertifikanın araya girmemesi ve bundan dolayı sayfa yasaklama sayfasına yönlendirme yapılmasının mümkün olmamasıdır.
- HTTP İnceleme Ayarları panelinde otomatik algılama checkbox'ının durumu pasif olarak belirtilmiş, ancak bu durumun etkili olup olmadığını bilmiyoruz.
- HTTPS İnceleme Ayarları panelinde otomatik algılama checkbox'ının durumu pasif olarak belirtilmiş, ancak bu durumun etkili olup olmadığını bilmiyoruz.
- Kaynak Adrese Göre Çalışma Modu panelinde HTTPS denetim ayarlarını yönetmek için kullanılan metin alanları ve butonlar.
- HTTPS Denetim Ayarlarında Kaynak Adrese Göre Çalışma Modu: Sertifika Değiştir seçili olduğunda Sayfa Yasaklama Ekranı gelecektir.
- Kaynak Adrese Göre Çalışma Modu: SNI seçiliyse sayfa yasaklama ekranı gelmeyecek ama kullanıcının sayfaya erişimi yine de engellenecektir. SNI modda engellenen HTTPS sayfalarda, yasak uyarı sayfasının gelmeme nedeni sertifikanın araya girmemesi ve bundan dolayı sayfa yasaklama sayfasına yönlendirme yapılmasının mümkün olmamasıdır.
- HTTP(S) Denetim Ayarlarında Kaynak Adrese Göre Çalışma Modu: Sertifika Değiştir seçili olduğunda Sayfa Yasaklama Ekranı gelecektir.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/web-filtreleme/https-denetim-ayarlari/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
