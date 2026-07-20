# DMZ Sunucu Yönetimi

## Kapsam

DMZ (Demilitarized Zone) silahtan arındırılmış bölgedir. DMZ’in amacı internete hizmet verecek sunuculara gelen trafiğin iç networkten izole edilmesidir. Örneğin; WEB, e-posta, FTP vb. sunucular bulunmaktadır.

## Menü yolu

- `DMZ Sunucu Yönetimi > DMZ Erişimleri > Kayıt Düzelme`

## Kullanım adımları

1. Durum seçimi yapın.
2. DMZ IP Arayüzü ve DMZ IP Adresi alanlarını doldurun.
3. NAT IP Arayüzü ve NAT IP Adresi alanlarını doldurun.
4. DMZ Türü seçimi yapın.
5. Açıklama alanını doldurun.
6. DMZ Sunucusu IP Adresi girin ve IPv4 seçeneğini etkinleştirin.
7. Erişim Denetimini 'Bu Ekrandan Yönet' seçeneğini etkinleştirin.
8. Durum'u seçin
9. DMZ Türünü seçin
10. Adres Ailesini seçin
11. DMZ IP Arayüzü seçin
12. DMZ IP Adresi seçin
13. NAT IP Arayüzü seçin
14. NAT IP Adresi seçin
15. Loglama durumunu seçin
16. Erişim Denetimini seçin
17. Açıklama alanına gerekirse bir açıklama girin
18. Durum'u seçin.
19. DMZ Türü'ni seçin.
20. Adres Ailesi'ni seçin.
21. DMZ IP Arayüzü'ni seçin.
22. DMZ IP Adresi'ni girin.
23. NAT IP Arayüzü'ni seçin.
24. NAT IP Adresi'ni girin.
25. Loglama özelliğini aktif edin veya pasif olarak bırakın.
26. Erişim Denetimi'ni seçin.
27. Açıklama alanına bilgi girin.
28. Geri dönme butonuna tıklayın.
29. Sayfanın yenilmesini istediğinizde Yenile butonuna tıklayın.
30. Durum seçeneğini aktif olarak belirleyin veya kapalı olarak bırakın.
31. Servisler seçeneğini istediğiniz servise göre ayarlayın.
32. Trafiği Logla seçeneğini açmak için checkbox'i işaretleyin veya kaplamak için işaretlemeyin.
33. Durum'u 'Aktif' olarak ayarlayın.
34. Trafiği Logla'yı 'Kapalı' olarak ayarlayın.
35. Erişecek Ağ'ı gerekli ağlarla güncelleyin.
36. Açıklama alanını gerekli bilgiyle doldurun.

## Alanlar

- `Durum` (Durum): DMZ sunucusunun durumu seçimi.
- `DMZ IP Arayüzü` (DMZ IP Arayüzü): DMZ sunucusunun IP adresi.
- `DMZ IP Adresi` (DMZ IP Adresi): DMZ sunucusunun IP adresi.
- `NAT IP Arayüzü` (NAT IP Arayüzü): NAT sunucusunun IP adresi.
- `NAT IP Adresi` (NAT IP Adresi): NAT sunucusunun IP adresi.
- `DMZ Türü` (DMZ Türü): DMZ sunucusunun türü seçimi.
- `Açıklama` (Açıklama): DMZ sunucusunun açıklaması.
- `Göster/Gizle` (Web Sunucu paneli): Tablo gösterimi seçeneği
- `Sayfa Başı Kayıt Sayısı` (Web Sunucu paneli): Sayfada görüntülenecek kayıtların sayısı
- `Erişecek Ağ` (Erişecek Ağ): DMZ erişimleri için kullanılacak ağ bilgilerini girer. Eğer boş bırakılırsa, varsayılan değer kullanılır.
- `Kişi Başı Maximum Bağlantı Sayısı` (Kişi Başı Maximum Bağlantı Sayısı): Kişi başına maksimum bağlantı sayısını girer. Eğer boş bırakılırsa, varsayılan değer kullanılır.
- `5 Saniyede Maximum Bağlantı Sayısı` (5 Saniyede Maximum Bağlantı Sayısı): 5 saniyede maksimum bağlantı sayısını girer. Eğer boş bırakılırsa, varsayılan değer kullanılır.
- `Zaman Dilimleri` (Zaman Dilimleri): Erişim için zaman dilimlerini girer. Eğer boş bırakılırsa, varsayılan değer kullanılır.

## Görünür kontroller

- `Yenile`: Ekrandaki verileri yeniden yükleme.
- `Ekle`: Yeni bir DMZ sunucusu ekleme.
- `Göster/Gizle`: Verileri göstere veya gizleme.
- `Sayfa Başı Kayıt Sayısı`: Sayfada gösterilecek kayıtların sayısı ayarlamak için.
- `Tamam`: Ekrandaki işlemleri tamamlama.
- `Filtrele`: Verileri filtrelemek için.
- `Filtreyi Temizle`: Filtreleri temizleme.
- `Aktif`: Durum Aktive Edin
- `DMZ Türü`: DMZ Sunucusu Tipi Seçin
- `IPv4`: Adres Ailesi IPv4 seçeneğini etkinleştirin
- `DMZ IP Arayüzü`: DMZ Sunucusu IP Arayüzünü Seçin
- `Pasif`: Loglama Aktive Edin
- `Erişim Denetimi`: Erişim Denetimini Seçin
- `Durum`: DMZ Sunucusunun Durumu Aktif Olup Olmadığını Belirler
- `Adres Ailesi`: IP Adresinin Ailesini Seçir (IPv4 veya IPv6)
- `DMZ IP Adresi`: DMZ Sunucusunun IP Adresini Seçir (IPv4 veya IPv6)
- `NAT IP Arayüzü`: NAT Sunucusunun IP Arayüzünü Seçir
- `NAT IP Adresi`: NAT Sunucusunun IP Adresini Seçir (IPv4 veya IPv6)
- `Loglama`: DMZ Sunucusundaki Loglamayı Aktif Olup Olmadığını Belirler
- `Açıklama`: Kayıtın açıklamasını girer.
- `Geri Dön`: Geri dönme butonu
- `+ Ekle`: Yeni kayıtlar ekleme butonu
- `Servisler`: DMZ erişimleri için kullanılacak servisleri seçer.
- `Trafiği Logla`: Trafiğin loglanıp loglanmadığını belirler.

## Uyarılar

- Her Yönden NAT Yap seçeneği kullanıldığında, her yönde NAT yapma işlemi gerçekleşir.
- Sadece WAN'dan NAT Yap seçeneği kullanıldığında, sadece WAN üzerinden NAT yapma işlemi gerçekleşir.
- Herhangi bir hata mesajı yok.
- Bu tabloda yazdığınız portlar dışındaki bütün portları erişime kapatacaktır. Hiçbir port erişimi yazmamanız durumunda, bütün portlara dışardan erişilebilecektir.
- Bağlantı sayısını kontrol edin ve gereksiz bağlantıları kapatın.
- Erişim Denetimi seçeneğindeki diğer seçeneklerin neler olduğunu belirtmek için ek bilgiye ihtiyacınız olabilir.
- Açıklama alanının tam olarak ne işe yaradığını belirtmek için ek bilgiye ihtiyacınız olabilir.
- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: DMZ IP Arayüzü, NAT IP Arayüzü
- Erişecek Ağ, Açıklama ve Zaman Dilimleri alanları boş bırakılarak varsayılan değerler kullanılır. Bu alanlara gerekli bilgileri girip kaydetmek gereklidir.
- Zaman Dilimleri alanında bir seçeneği belirleyememiştim.
- Servisler alanındaki seçeneklerin tam listesini göremedim.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/dmz-yonetimi/dmz-sunucu-yonetimi/
- Güven puanı: 0.94
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
