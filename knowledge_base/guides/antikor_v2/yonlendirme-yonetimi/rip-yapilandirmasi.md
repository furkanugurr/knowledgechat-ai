# RIP Yapılandırması

## Kapsam

RIP (Router Information Protocol), uzaklık vektör algoritmasıyla çalışan ve yönlendirmeleri hesaplamak için Bellman-Ford algoritmasını kullanmaktdır. RIP, yönlendirici cihazların tablosunda Yönetim Mesafesi (Administrative Distance) 120 olarak yer alır. RIP yönlendiriciler, en iyi yol seçimini yaparken sadece geçtiği cihaz (hop) sayısına  bakar. RIP en fazla 15 hop’u kabul eder. Bu sayı aşıldığı zaman (yani 16. hopa gelince) destination unreachable (kaynak bulunamadı) hatasını verir.

## Menü yolu

- `Ayarlar > Komşular Yeni Kayıt`
- `Paylaşılan Ağlar > Komşular > Yeni Kayıt`
- `Komşular > Parolalar > RIP Yapılandırması`
- `RIP Yapılandırması > RIPng`
- `RIP Yapılandırması > RIP Neighbour`

## Kullanım adımları

1. RIPv2 seçeneğini etkinleştirin veya devre dışı bırakın.
2. Router-id'yi girmek için IP adresi girin.
3. Otomatik Özetle seçeneğini etkinleştirin veya devre dışı bırakın.
4. Komsuyu düzenleme için Düzenle butonuna tıklayın.
5. Komsuyu silmek için Sil butonuna tıklayın.
6. Aktif durumu seçmek için checkbox'ı işaretleyin.
7. Durum kutusunu seçmek için checkbox'ı işaretleyin.
8. IPv4 adresini girin: 192.168.33.111
9. RIP yapılandırması hakkında açıklama yapın: RIP Yapılandırması Komsular
10. Kaydet butonuna tıklayın.
11. Durum checkbox'una tıklayarak aktif durumu etkinleştirin.
12. Parola zinciri için gerekli düğmeleri kullanarak parola zincirlerini ekleme veya düzenleme yapın.
13. MD5 Doğrulama checkbox'una tıklayarak MD5 doğrulamasını etkinleştirin.
14. Açıklama field'ına RIP Yapılandırması Parola yazarak açıklamanızı girin.
15. Router-id alanına IPv6 adresi girin.
16. Ayarları kaydetmek için 'Kaydet' düğmesine tıklayın.
17. Aktif durumu seçmek için 'Durum' alanındaki kutuyu işaretleyin.
18. Ağ adını 'Network' alanında girmek veya değiştirmek için metin kutusuna tıklayın ve yeni değer girin.

## Alanlar

- `RIPv2` (Ayarlar): Router Information Protocol v2'nin etkin olup olmadığını gösteren bir kontrol.
- `Router-id` (Ayarlar): Router'ın tanımlayıcısı için kullanılan bir IP adresi.
- `Otomatik Özetle` (Ayarlar): RIP verilerinin otomatik olarak özetlenip özetlenmediğini gösteren bir kontrol.
- `Göster/Gizle` (Komşular paneli): Paneli göster veya gizleme seçeneği
- `Sayfa Başı Kayıt Sayısı` (Komşular paneli): Sayfada görüntülenecek kayıtların sayısı
- `Durum` (Durum): Aktif durumu seçmek için kullanılan checkbox.
- `IP Adresi` (IP Adresi): IPv4 adresini girilen alan.
- `IPv4 Adresi` (IPv4 paneli): IPv4 adresini girer
- `Açıklama` (Açıklama paneli): RIP yapılandırması hakkında açıklama yapar
- `Varsayılan Ağ Geçidi Yayını` (Paylaşılan Ağılar panelinde): varsayılan ağ geçidi yayınının aktif olup olmadığını gösteren kontrol
- `Network` (Network): Eylem: Ağ adını girer veya değiştirir.
- `RIP Neighbour` (section_name): RIP komşularının ve yönlendirme bilgilerinin izlendiği ekran.

## Görünür kontroller

- `RIP`: Router Information Protocol'ün yapılandırması için kullanılan bir sekme.
- `RIPng`: RIPv2'nin genişletilmiş versiyonu için kullanılan bir sekme.
- `RIP Neighbour`: Router'lar arasındaki komşuluk ilişkileri için kullanılan bir sekme.
- `+ Ekle`: Yeni komsu ekleme
- `Düzenle`: Komsuyu düzenleme
- `Sil`: Komsuyu silme
- `İptal`: İşlemin iptali için kullanılan düğme.
- `Kaydet`: Kaydedilen bilgileri kaydetmek için kullanılan düğme.
- `Durum`: Aktif durumu seçmek için kullanılan checkbox.
- `Zincir 1`: Parola zinciri ekleme veya düzenleme için kullanılan düğme.
- `Zincir 2`: Parola zinciri ekleme veya düzenleme için kullanılan düğme.
- `Zincir 3`: Parola zinciri ekleme veya düzenleme için kullanılan düğme.
- `MD5 Doğrulama`: MD5 doğrulama seçeneğini etkinleştirmek için kullanılan checkbox.
- `Yenile`: Verileri yeniden yüklemek için kullanılan düğme
- `Ekle`: Yeni bir ağ ekleme işlemi için kullanılan düğme

## Uyarılar

- Bu ekran, RIP Yapılandırması için yeni bir kaydı oluşturmak için kullanılır. Eğer bir parola zinciri veya doğrulama gereksinimleri varsa, bu alanları doldurmanız gerekmektedir.
- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: Durum

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/yonlendirme-yonetimi/rip-yapilandirmasi/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
