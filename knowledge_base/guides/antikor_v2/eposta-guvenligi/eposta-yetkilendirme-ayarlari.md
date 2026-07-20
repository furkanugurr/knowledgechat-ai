# E-Posta Yetkilendirme Ayarları

## Kapsam

E-posta sunucuları için genel, gönderen/alıcı adres ve harici SMTP sunucu yetkilerini içermektedir.

## Menü yolu

- `E-Posta Yetkilendirme Ayarları > SMTP Genel Yetkiler`
- `Harici SMTP Sunucu Yetkileri`

## Kullanım adımları

1. SMTP HELO/EHLO Kontrolleri
2. SMTP HELO/EHLO Makine adı, FQDN değilse reddet
3. SMTP HELO/EHLO Makine adının DNS A veya MX kaydı yoksa reddet
4. E-Posta Sunucuları
5. Gönderici Adres Kontrolleri
6. Gönderen adresindeki alan adı FQDN değilse reddet
7. Gönderen adresindeki alan adının DNS A veya MX kaydı yoksa reddet
8. SMTP HELO/ EHLO Makine adı biçimi geçersizse reddet
9. SMTP HELO/ EHLO Makine adı, FQDN değilse reddet
10. SMTP HELO/ EHLO Makine adının DNS A veya MX kaydı yoksa reddet
11. Durum seçeneğini aktif hale getirin.
12. Sıra no alanına bir değer girin.
13. Adres ailesini IPv4 olarak seçin.
14. Yetki kararını 'İzin ver' olarak belirtin.
15. Açıklama metnini girmek isterseniz bu alanın altına yazabilirsiniz.
16. DNS/Ters DNS kaydı yoksa veya bağlanan IP ile tutarsız ise reddet özelliğini açın.
17. Gönderici Adres Kontrolleri panelinde 'Gönderen adresindeki alan adı FQDN değilse reddet' ve 'Gönderen adresindeki alan adının DNS A veya MX kaydı yoksa reddet' seçeneklerini açın.
18. Alıcı adresindeki alan adı FQDN değilse reddet seçeneğini kontrol edin ve gerekirse açıklayın veya kapatin.
19. Alıcı adresindeki alan adının DNS A veya MX kaydı yoksa reddet seçeneğini kontrol edin ve gerekirse açıklayın veya kapatin.
20. SMTP komut sıralamasına uymayan bağlantıları reddet özelliğini açın.
21. Gönderen ve alıcı adresler hakkında karar(İzin Ver, Karantinaya Al, …) verilmektedir.
22. Önemli Not: Gönderen adres yetkilerine mutlaka e-posta sunucusu ve domain tanımı yetkili olarak eklenmelidir. Aksi takdirde kullanıcı e-posta gönderemez.
23. Durum alanındaki checkbox'ı seçerek yetkinin aktif olup olmadığını belirler.
24. Sıra No alanına gönderen adres sırasını girer.
25. Adres Tanımı alanına gönderen adres tanımını girer.
26. Karar dropdown listesinden yetki kararını seçer.
27. Açıklama alanına yetki açıklamasını girer.
28. Kaydet düğmesini tıklayarak yeni yetki kaydını kaydedir.
29. Durum'u 'Aktif' olarak seçin.
30. Sıra No alanına bir sıra numarası girin.
31. Adres Tanımı alanına bir adres tanımlı girin.
32. Karar seçeneğini 'İzin ver' olarak ayarlayın.
33. Açıklama alanına gerekli açıklamaları girin.
34. Kaydet butonuna tıklayarak kaydedin.
35. SMTP sunucusu yetkilerini yönetmek için 'Harici SMTP Sunucu Yetkileri' paneline gidin.
36. Seçilen SMTP sunucusunun detaylarını düzenleme için '+ Ekle' düğmesine tıklayın.

## Alanlar

- `Sıra No` (Durum paneli): Yetki sırası no
- `Adres Ailesi` (Adres Ailesi paneli): Adres ailesi seçimi
- `Sunucu Adresi` (Sunucu Adresi paneli): SMTP sunucusu adresi
- `Karar` (Karar paneli): Yetki karar seçimi
- `Açıklama` (Açıklama paneli): Açıklama metni
- `Durum` (Gönderen Adres Yetkileri): Gönderen veya alıcı adresin durumu seçimi.
- `Adres Tanımı` (Gönderen Adres Yetkileri, Alıcı Adres Yetkileri): Gönderen veya alıcı adres tanım bilgisi.
- `Göster/Gizle` (Panel): Sayfa içeriğini göstere veya gizleme seçenekleri
- `Sayfa Başı Kayıt Sayısı` (Panel): Sayfada gösterilecek kayıtların sayısı

## Görünür kontroller

- `SMTP HELO/EHLO Kontrolleri`: SMTP doğrularken HELO/EHLO isimlerinin FQDN standartlarında olması hemen hemen zorunludur. HELO/EHLO’dan dönen İsimlerin kesinlikle IP çözüyor olması gerekir.
- `SMTP HELO/EHLO Makine adı, FQDN değilse reddet`: SMTP doğrularken HELO/EHLO isimlerinin FQDN standartlarında olması hemen hemen zorunludur. HELO/EHLO’dan dönen İsimlerin kesinlikle IP çözüyor olması gerekir.
- `SMTP HELO/EHLO Makine adının DNS A veya MX kaydı yoksa reddet`: SMTP doğrularken HELO/EHLO isimlerinin FQDN standartlarında olması hemen hemen zorunludur. HELO/EHLO’dan dönen İsimlerin kesinlikle IP çözüyor olması gerekir.
- `E-Posta Sunucuları`: DNS/Ters DNS kaydı yoksa veya bağlanılan IP ile tutarsız ise reddet
- `Gönderici Adres Kontrolleri`: Gönderen adresindeki alan adı FQDN değilse reddet
- `Gönderen adresindeki alan adının DNS A veya MX kaydı yoksa reddet`: SMTP doğrularken HELO/EHLO isimlerinin FQDN standartlarında olması hemen hemen zorunludur. HELO/EHLO’dan dönen İsimlerin kesinlikle IP çözüyor olması gerekir.
- `SMTP HELO/ EHLO Makine adı biçimi geçersizse reddet`: SMTP doğrularken HELO/EHLO isimlerinin FQDN standartlarında olması hemen hemen zorunludur. HELO/EHLO’dan dönen İsimlerin kesinlikle IP çözüyor olması gerekir.
- `SMTP HELO/ EHLO Makine adı, FQDN değilse reddet`: SMTP doğrularken HELO/EHLO isimlerinin FQDN standartlarında olması hemen hemen zorunludur. HELO/EHLO’dan dönen İsimlerin kesinlikle IP çözüyor olması gerekir.
- `SMTP HELO/ EHLO Makine adının DNS A veya MX kaydı yoksa reddet`: SMTP doğrularken HELO/EHLO isimlerinin FQDN standartlarında olması hemen hemen zorunludur. HELO/EHLO’dan dönen İsimlerin kesinlikle IP çözüyor olması gerekir.
- `Durum`: Yetki durumu
- `İptal`: İptal etme
- `Kaydet`: Kaydetme
- `DNS/Ters DNS kaydı yoksa veya bağlanan IP ile tutarsız ise reddet`: E-posta sunucularında DNS/Ters DNS kaydı ve bağlanan IP kontrol edilir. Bu bilgilerin olmaması veya tutarsız olması halinde gelen isteklerin reddedilmesi için bu alandaki özellik açılmalıdır.
- `Gönderen adresindeki alan adı FQDN değilse reddet`: Gönderici adresindeki alan adının FQDN kontrolü için özellik açma seçeneği
- `Alıcı adresindeki alan adı FQDN değilse reddet`: Alıcı adresindeki alan adının FQDN kontrolü için açık veya kapalı durumunu belirler.
- `Alıcı adresindeki alan adının DNS A veya MX kaydı yoksa reddet`: Alıcı adresindeki alan adının DNS A veya MX kaydı kontrolü için açık veya kapalı durumunu belirler.
- `SMTP komut sıralamasına uymayan bağlantıları reddet`: SMTP komut sıralamasına uymayan bağlantıları kontrol edilmesi ve reddedilmesi için bu özellik açılmalıdır.
- `+ Ekle`: Yeni bir gönderen veya alıcı adres ekleme işlemi başlatır.
- `Düzenle`: Seçilen gönderen veya alıcı adresin detaylarını düzenleme işlemi başlatır.
- `Sil`: Seçilen gönderen veya alıcı adresi silme işlemi başlatır.
- `Yenile`: Sayfayı yeniden yükleme işlemi başlatır.

## Uyarılar

- Gönderen adres yetkilerine mutlaka e-posta sunucusu ve domain tanımı yetkili olarak eklenmelidir. Aksi takdirde kullanıcı e-posta gönderemez.
- Alıcı adres yetkilerine mutlaka domain tanımı yetkili olarak eklenmelidir. Aksi takdirde kullanıcı dışarıdan e-posta alamaz.
- Adres Tanımı ve Açıklama alanlarının durumu belirsizdir.
- Karar seçeneği 'İzin ver' dışında başka seçenekler olabilir.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/eposta-guvenligi/eposta-yetkilendirme-ayarlari/
- Güven puanı: 0.88
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
