# OSPF Yapılandırması

## Kapsam

OSPF (Open Shortest Path First) , yaygın olarak kullanılan bir iç yönlendirme protokolüdür. Genellikle büyük ağlarda kullanılır ve bir ağdaki yönlendiriciler arasında en kısa yol (shortest path) hesaplamak için SPF (Shortest Path First) algoritmasını kullanır. SPF algoritması, ağ topolojisini temel alarak her yönlendirici için en kısa yolu belirler ve bu yolları kullanarak ağ üzerindeki rotaları hesaplar.

## Menü yolu

- `OSPF Yapılandırması > OSPFv2`
- `OSPF Yapılandırması > OSPF Neighbour`
- `Ayarlar > OSPFv2 Paylaşılan Ağlar Yeni Kayıt`
- `OSPFv2 > OSPFv3 > OSPF Neighbour`
- `OSPFv3 Yapılandırması > OSPFv3 Paylaşılan Ağlar Yeni Kayıt`

## Kullanım adımları

1. Router ID'nin IPv4 adresini girin ve Kaydet düğmesine tıklayın.
2. Parolalar panelinde yeni bir parola ekleme veya düzenleme işlemi yapmak için '+ Ekle' ve 'Düzenle' butonlarını kullanabilirsiniz.
3. Seçilen parolanın MD5 doğrulanması durumunu kontrol etmek için 'MD5 Doğrulama' checkbox'unu kontrol edebilirsiniz.
4. OSPF Neighbour detayı görüntülemek için 'OSPF Neighbour Detail' sekmesine tıklayın.
5. Ağda OSPF komşularının durumu ve hangi rotaların alındığı görüntülemek için 'OSPF Route' sekmesine tıklayın.
6. Durum seçeneğini aktif olarak ayarlayın.
7. Doğrulama seçeneğini 'Yok' olarak belirtin.
8. Durum seçeneğini belirleyin ve 'Aktif' veya 'Pasif' olarak ayarlayın.
9. Parolayı girin.
10. MD5 doğrulama durumunu seçin ve 'Var' veya 'Pasif' olarak ayarlayın.
11. Açıklamayı girin.
12. Kaydet butonuna tıklayarak bilgileri kaydedin.
13. Durum seçeneğini aktif olarak ayarlayın veya pasif olarak bırakın.
14. Açıklama alanına OSPFv2 Komşular yazın.
15. Router-Id'yi girin ve Kaydet düğmesine tıklayın.
16. Aktif durumda olan OSPFv3 parolasını düzenleyin veya silin.
17. Yeni bir OSPFv3 parolası ekleyin.
18. Network ID'sini LAN1 olarak girin.
19. Area numarasını 2 olarak ayarlayın.
20. MD5 doğrulama durumunu seçin.
21. Kaydet butonuna tıklayın.
22. IP Adresi alanına OSPF komşu ağının IP adresini girin.
23. Açıklama alanına OSPF komşu ağının açıklamasını girin.
24. Kaydet düğmesine tıklayarak bilgileri kaydedin.

## Alanlar

- `Router-Id IPv4` (Ayarlar paneli): Router ID'nin IPv4 adresini içeren alan.
- `IP Adresi` (Paylaşılan Ağlar paneli): Paylaşılan ağın IP adresini içeren alan.
- `Parola` (Parolalar paneli): OSPv2 parolası.
- `MD5 Doğrulama` (Parolalar paneli): Parolanın MD5 doğrulanması durumu.
- `Area` (Area): Ağın hangi area numarasına ait olduğu belirtilir.
- `Durum` (Durum): Parola durumu (aktif/pasif).
- `Açıklama` (Açıklama): Parola açıklaması.
- `Router-Id` (Ayarlar panelinde): Router ID'si girilmesi gereken alan.
- `Network ID` (Paylaşılan Ağılar panelinde): Network ID'si girilmesi gereken alan.

## Görünür kontroller

- `Kaydet`: Ayarları kaydetmek için kullanılan düğme.
- `Yenile`: Sayfayı yeniden yüklemek için kullanılan düğme.
- `+ Ekle`: Paylaşılan ağ ekleme işlemi için kullanılan düğme.
- `Düzenle`: Seçilen parolayı düzenlemek için kullanılır.
- `Sil`: Seçilen parolayı silmek için kullanılır.
- `OSPF Neighbour Detail`: Ağda OSPF komşularının durumu ve hangi rotaların alındığı görülebilir.
- `OSPF Route`: Ağda OSPF komşularının durumu ve hangi rotaların alındığı görülebilir.
- `Durum`: Ağın durumu (aktif/pasif) belirler.
- `Doğrulama`: Parola doğrulama seçeneği (Yok/MD5/Plain) belirler.
- `İptal`: Kaydettiğiniz bilgileri iptal etme.
- `Ekle`: Yeni bir parola veya komşu ekleme
- `Filtrele`: Parola listesini filtreleme
- `Filtreyi Temizle`: Parola listesinin filtresini temizleme

## Uyarılar

- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: Durum

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/yonlendirme-yonetimi/ospf-yapilandirmasi/
- Güven puanı: 0.94
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
