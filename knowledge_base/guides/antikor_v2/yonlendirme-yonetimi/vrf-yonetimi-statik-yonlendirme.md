# VRF Yönetimi / Statik Yönlendirme

## Kapsam

Bu sayfada VRF Yönetimi – Statik Yönlendirme işlemleri gerçekleştirilmektedir. VRF (Virtual Routing and Forwarding), aynı cihaz üzerinde birden fazla mantıksal yönlendirme tablosu oluşturulmasına olanak tanır. Bu sayede farklı ağlar birbirinden izole edilerek yönetilebilir.

## Menü yolu

- `VRF Yönetimi / Statik Yönlendirme`

## Kullanım adımları

1. Statik yönlendirme işlemlerini gerçekleştirmek için VRF Yönetimi ekrandına gidin.
2. Yeni bir VRF kaydı oluşturmak için '+ Ekle' butonuna tıklayın.
3. VRF Adı: Oluşturulacak VRF yapısına ait isim bilgisidir.
4. VRF Numarası: VRF’i sistem içerisinde ayırt etmek için kullanılan sayısal tanımdır.
5. Açıklama: VRF’in kullanım amacı veya ait olduğu ağ yapısı hakkında bilgilendirici açıklama alanıdır.
6. Statik Yönlendirme Yeni Kayıt
7. Bu ekranda tanımlı olan VRF'ler listelenmektedir. Her VRF, kendisine ait bağımsız bir yönlendirme alanını temsil eder.
8. İlgili VRF altında statik yönlendirme (rota) tanımlamak için, satır üzerinde bulunan Erişimler butonuna tıklanır. Bu işlem sonrasında seçilen VRF'e ait statik yönlendirme kayıtlarının bulunduğu ekrana geçilir.
9. Statik yönlendirme yeni kayıt işlemleri, yalnızca seçili VRF altında gerçekleştirilir. Bu sayede her VRF için ayrı ve izole statik rota tanımları yapılabilir.
10. Durum kutusunu işaretleyerek yönlendirme kaydını etkin hale getirin.

## Alanlar

- `#` (VRF Yönetimi / Statik Yönlendirme paneli): Kayıtların sıralama numarası.
- `VRF Adı` (VRF Yönetimi / Statik Yönlendirme paneli): VRF'lerin isimleri.
- `VRF Numarası` (VRF Yönetimi / Statik Yönlendirme paneli): VRF'lerin numaraları.
- `Açıklama` (VRF Yönetimi / Statik Yönlendirme paneli): Kayıtların açıklamaları.
- `Hedef Ağ` (Statik Yönlendirme paneli): Statik yönlendirme hedef ağını girin. (IPv4 veya IPv6 formatında.)
- `Ağ Geçidi` (Statik Yönlendirme paneli): Ağ geçidini girin.

## Görünür kontroller

- `Yenile`: Ekranda gösterilen verileri yeniden yükleme işlemi.
- `+ Ekle`: Yeni bir VRF kaydı ekleme işlemi.
- `XLS`: Verileri XLS formatında indirme işlemi.
- `CSV`: Verileri CSV formatında indirme işlemi.
- `PDF`: Verileri PDF formatında indirme işlemi.
- `Göster/Gizle`: Gösterecek veya gizlenecek verilerin seçimi.
- `Sayfa Başı Kayıt Sayısı`: Sayfada gösterilecek kayıtların sayısı.
- `Tamam`: Seçilen sayfayı onaylama işlemi.
- `Filtrele`: Verilerin filtrelenmesi işlemi.
- `Filtreyi Temizle`: Filtrelerin temizlenmesi işlemi.
- `İptal`: Ekrandaki işlemlerin iptali için kullanılır.
- `Kaydet`: Oluşturulan VRF kaydı aktif hale getirilmesi ve ekrandan çıkılması için kullanılır.
- `Erişimler`: Seçilen VRF'e ait statik yönlendirme kayıtlarına erişim sağlama.
- `Durum`: Yönlendirme kaydını etkin hale getirmek için işaretlenir.
- `Adres Ailesi`: IPv4 veya IPv6 adres ailesini seçmek için kullanılır.
- `Yönlendirme`: Ağ geçidi veya arayüz yönlendirme türünü seçmek için kullanılır.

## Uyarılar

- panel_name

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/yonlendirme-yonetimi/vrf-yonetimi-statik-yonlendirme/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
