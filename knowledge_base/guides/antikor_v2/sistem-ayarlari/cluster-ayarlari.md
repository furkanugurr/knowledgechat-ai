# Cluster Ayarları

## Kapsam

Cluster, benzer bir amaç için belirli bir konfigürasyon yapılarak sunucuların yedekli çalışmasını sağlayan servistir. Antikor, 2 sunucuya kadar cluster yapısını aktif/pasif olarak desteklemektedir. Antikor, yüksek erişilebilirlik cluster yapısına uygun çalışabilmektedir. Yani clusterdaki bir sunucunun donanım ya da yazılım problemi oluştuğunda diğer bir sunucunun otomatik olarak devreye girmesidir. Bu durum network açısından sürekliliği sağlamaktadır.

## Menü yolu

- `Sistem Ayarları > Cluster Ayarları`
- `Sistem Ayarlari > Cluster Ayarları`

## Kullanım adımları

1. Görev Değiştir butonu aktif cihazda tıklatılmalıdır.
2. Pasif sunucunun durumunu kontrol edin.
3. Aktif sunucunun durumunu kontrol edin.
4. Cluster ayarlarını yönetmek için 'Çalışma Modu Ayarları' sekmesine gidin.
5. Cluster ayarlarını yönetmek için 'Senkronizasyon Ayarları' sekmesine gidin.
6. Ethernet ayarlarını yönetmek için 'Ethernet Ayarları' sekmesine gidin.
7. El sıkışma ayarlarını yönetmek için 'El Sıkışma Ayarları' sekmesine gidin.
8. Bağımsız, Aktif - Pasif, Aktif - Aktif seçeneklerinden birini seçin.
9. Aktif ve Pasif seçeneklerinden birini seçin.
10. Diğer Cihaz Sağlıklı Olursa Görevi Devret
11. Bağlantı Durumları Senkronizasyonu
12. Güncelleme Paketi Senkronizasyonu
13. Merkezden Gelen Değişiklikleri Senkronize Et
14. Ethernet Kullanım Türü seçeneğini 'Bağımsız' olarak ayarlayın.
15. Cluster Durumu kontrol edilmelidir.
16. Erişilemiyor yazan cihazın ayarları ve bağlantıları kontrol edilmelidir.

## Alanlar

- `Antikor NGFW` (Cluster Durumu panelinde): Aktif sunucunun host adı ve IP adresi.
- `Cluster Ayarları` (Çalışma Modu Ayarları): Cluster ayarlarının çalışma modunu belirler. Bağımsız, Aktif-Pasif ve Aktif-Aktif seçenekleri mevcuttur.
- `Başlangıç Görevi` (Çalışma Modu Ayarları): Cluster ayarlarının başlangıç görevini belirler. Aktif ve Pasif seçenekleri mevcuttur.
- `Canlılık Paketi Gönderim Sıklığı` (Çalışma Modu Ayarları): Cluster ayarlarının canlılık paketi gönderim sıklığını belirler. Mesafe birimi ms'dir.
- `Canlılık Paketi Dinleme Zaman Aşımı` (Çalışma Modu Ayarları): Cluster ayarlarının canlılık paketi dinleme zaman aşımını belirler. Mesafe birimi ms'dir.
- `Diğer Cihaz Sağlıklı Olursa Görevi Devret` (Senkronizasyon Ayarları): Cluster ayarlarının diğer cihaz sağlıktan dolayı görev devretme özelliğini belirler.
- `Bağlantı Durumları Senkronizasyonu` (Senkronizasyon Ayarları): Cluster ayarlarının bağlantı durumları senkronizasyonunu belirler.
- `Güncelleme Paketi Senkronizasyonu` (Senkronizasyon Ayarları): Cluster ayarlarının güncelleme paketi senkronizasyonunu belirler.
- `Merkezden Gelen Değişiklikleri Senkronize Et` (Senkronizasyon Ayarları): Cluster ayarlarının merkezden gelen değişiklikleri senkronize etme özelliğini belirler.
- `Ethernet Kullanım Türü` (Ethernet Ayarları): Ethernet ayarlarının kullanım türünü belirler. Paylaşımı ve Bağımsız seçenekleri mevcuttur.
- `Senkronizasyon Etherneti` (Ethernet Ayarları): Cluster ayarlarının senkronizasyon etkinliğini belirler. Seçenek bge1 (CLUSTER) gibi bir ağ kartı adı olabilir.
- `IP Adresi` (Ethernet Ayarları): Cluster ayarlarının IP adresini belirler. IPv4 formatında bir adres olmalıdır.
- `Diğer Cihaz IP Adresi` (Ethernet Ayarları): Cluster ayarlarının diğer cihazın IP adresini belirler. IPv4 formatında bir adres olmalıdır.
- `VHID Değeri` (El Sıkışma Ayarları): El sıkışma ayarlarının VHID değerini belirler.
- `Ön Tanımlı Anahtar` (El Sıkışma Ayarları): El sıkışma ayarlarının ön tanımlı anahtarı girilmesini sağlar.
- `Diğer Cihazın Lisans Anahtarı` (El Sıkışma Ayarları): El sıkışma ayarlarının diğer cihazın lisans anahtarını girilmesini sağlar.
- `Diğer Cihazın Lisans Anahtarları` (El Sıkışma Ayarları paneli): Diğer cihazın lisans anahtarı girecek alan

## Görünür kontroller

- `Görev Değiştir`: Aktif cihazın rolünü değiştirip Pasif yapar.
- `Yeniden Senkronize Et`: Pasif sunucuda tüm tanımların uygulanması işlemi otomatik olarak tetikler.
- `Pasif`: Pasif sunucunun durumu.
- `Aktif`: Aktif sunucunun durumu.
- `Çalışma Modu Ayarları`: Cluster ayarlarının çalışma modunu belirlemek için kullanılan bir sekme.
- `Senkronizasyon Ayarları`: Cluster senkronizasyon ayarlarını yönetmek için kullanılan bir sekme.
- `Ethernet Ayarları`: Ethernet ayarlarını yönetmek için kullanılan bir sekme.
- `El Sıkışma Ayarları`: El sıkışma ayarlarını yönetmek için kullanılan bir sekme.
- `Cluster Ayarları`: Bağımsız, Aktif - Pasif, Aktif - Aktif
- `Başlangıç Görevi`: Aktif, Pasif
- `Diğer Cihaz Sağlıklı Olursa Görevi Devret`: If another device is healthy, the task will be suspended.
- `Bağlantı Durumları Senkronizasyonu`: Synchronization of connection status.
- `Güncelleme Paketi Senkronizasyonu`: Synchronization of update package.
- `Merkezden Gelen Değişiklikleri Senkronize Et`: Merkezden Gelen Değişiklikleri Senkronize Et
- `Ethernet Kullanım Türü`: Ethernet kullanımlarını paylaşım veya bağımsız olarak ayarlamak için.
- `Bağımsız`: Ethernet kullanımlarını bağımsız olarak ayarlamak için.
- `Diğer Cihazın Lisans Anahtarını Doğrula`: Diğer cihazın lisans anahtarını doğrulayan buton

## Uyarılar

- Cluster ayarları varsayılanda çalışma modu bağımsız olarak gelmekte ve Diğer Cihazın Lisans Anahtarı Doğrulanmamış! Lütfen doğrulayınız. uyarısı yer almaktadır.
- İki cihaza verilecek IP adreslerinin aynı IP bloğundan olması gerekmektedir. Örneğin bir sunucunun senkronizasyon IP adresi 10.10.10.11/24 ise diğerinin IP adresi karşıdaki sunucudan farklı ama aynı IP bloğunda olan 10.10.10.12/24 olabilir.
- İki cihaza verilecek IP adreslerinin aynı IP bloğundan olması gerekmektedir.
- Cluster Senkronizasyon uygulandıktan başlangıç görevi aktif olarak seçilecek olan cihazın ayarlarının(ethernet atama da dahil) başlangıç görevi pasif olarak seçilecek cihaza basılacağından; Antikorlara doğrudan erişim sağlayabilmek için iki cihazda da Yönetim Paneli Ayarlarından Bağımsız Yönetim altyapısı açılarak yönetim arayüzü oluşturulmalıdır.
- Ayarlar kaydedildikten sonra Diğer Cihazın Lisans Anahtarını Doğrula butonu ile test edilmelidir. Ayarlar doğru olmadığı müddetçe cluster senkronizasyonu yapılamayacaktır. İki cihazda da paket sürüm listesi kontrol edilip, paket versiyonlarının aynı olduğu görülmelidir.(İki cihazda da son güncelleştirmeler alınmış olmalıdır.)
- Ayarlardaki hata faktörü sıfır olduğundan, cluster senkronizasyonu yapılamamıştır. Ayarlar doğru olmalıdır.
- İki cihazın ethernet port sayısı aynı olmalıdır ve doğrudan bir kablo bağlantısı olması gerekmektedir.
- Pasif sunucunun durumunu kontrol etmek için 'Pasif' butonuna tıklayın.
- Aktif sunucunun durumunu kontrol etmek için 'Aktif' butonuna tıklayın.
- Ethernet Kullanım Türü seçeneği 'Paylaşımı' ve 'Bağımsız' seçenekleri arasında bir seçim yapabilir.
- Senkronizasyon Etherneti seçeneği bge1 (CLUSTER) gibi bir ağ kartı adı olabilir.
- Model aynı etiketi control ve field olarak sınıflandırdı; yapılandırma değeri olan field korundu: Ön Tanımlı Anahtar
- Cluster ayarları tamamlanmış olduğundan, iki cihazda tanımlar uygulanması beklenir. Ancak bu durumun görüntüdeki ekranın sonucu değildir ve kontrol edilmelidir.
- İki cihaz arasında senkronizasyon amaçlı kullanılmak üzere doğrudan bir kablo bağlantısı olması gerekmektedir.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/sistem-ayarlari/cluster-ayarlari/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
