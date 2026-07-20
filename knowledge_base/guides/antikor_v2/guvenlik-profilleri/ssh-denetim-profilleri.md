# SSH Denetimi

## Kapsam

title: SSH Denetim Profilleri —

## Menü yolu

- `SSH Denetim Profilleri — SSH Denetimi`
- `/kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/guvenlik-profilleri/ssh-denetim-profilleri/`

## Kullanım adımları

1. Adı ve Açıklama alanlarını doldurun.
2. Adı alanına SSH denetim profili adını girin.
3. SSH Tünelleme ve SSH Dosya Transferi (SFTP) seçeneklerini istediğiniz şekilde ayarlayın.
4. Servisler seçeneğini istediğiniz servise göre ayarlayın.
5. Açıklama alanına SSH denetim profili hakkında açıklama yapın veya boş bırakın.

## Alanlar

- `SSH İstemci IP adresi` (İstemci paneli): 192.168.100.x
- `SSH Sunucusu/IP adresi` (Sunucu paneli): 193.255.x.z
- `Adi` (Servisler): SSH Denetim Profilleri adı girilecek alan
- `Açıklama` (Açıklama): SSH Denetim Profilleri açıklaması girilecek alan
- `Adı` (Adı): SSH denetim profili adını girin. Bu alan boş bırakılamaz ve bir ad belirtilmelidir.

## Görünür kontroller

- `Yenile`: Ekranda listeyi yenileyen buton
- `+ Ekle`: SSH Denetim Profilleri ekleyen buton
- `Tanımları Uygula 2`: Ekranda tanımların uygulanmasını sağlayan buton
- `Durum`: SSH denetim profili durumu aktif etmek için kullanılır.
- `SSH Tünelleme`: SSH tünelleme özelliğini engelleme veya açma seçeneği.
- `SSH Dosya Transferi (SFTP)`: SSH dosya transferi (SFTP) özelliğini engelleme veya açma seçeneği.
- `Servisler`: SSH denetim profili için kullanılacak servisleri seçmek için kullanılır.

## Uyarılar

- IP adresleri örnek olarak verilmiştir.
- Sadece password auth ile bağlanılan SSH Sunucuları için ayar yapılabilmektedir. (Public Key olmamalıdır.)
- Kurallarda seçilen seçeneklerden bağımsız olarak bağlanılacak olan Sunucu/İstemci için Shell bağlantısı her zaman yapılmalıdır.
- SSH Denetim Servisi sadece "password authentication" yöntemini desteklemektedir. Bu nedenle, diğer kimlik doğrulama yöntemlerini kullanan bağlantılar, bu servise dahil edilmemelidir.
- IP adresleri örnek olarak verilmiştir. Sadece password auth ile bağlanılan SSH Sunucuları için ayar yapılabilmektedir.
- Ekle butonuna basıldığında açılan pencerenin detayları hakkında bilgi yoktur.
- Açıklama alanındaki metinlerin tamamı okunamamıştır.
- SSH Tünelleme ve SSH Dosya Transferi (SFTP) seçeneklerinin durumunu ayarlamak için hangi butonu kullanacağınızı belirleyemiyoruz.
- Servisleri seçmek için hangi butonu kullanacağınızı belirleyemiyoruz.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/guvenlik-profilleri/ssh-denetim-profilleri/
- Güven puanı: 0.94
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
