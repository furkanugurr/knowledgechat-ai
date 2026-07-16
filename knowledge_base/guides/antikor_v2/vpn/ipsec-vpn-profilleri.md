# IPSec VPN Profilleri

## Kapsam

Bu bölüm, IPSec VPN ayarları için oluşturulan profil seçeneklerini içermektedir.

## Menü yolu

- `Yeni Kayıt Ekle > Faz 1`
- `Faz 2 > Ölü Bağlantı Saptama`

## Kullanım adımları

1. Yeni bir IPSec VPN profilini eklemek için '+ Ekle' butonuna tıklayın.
2. Profil adını girin.
3. Durumu seçin veya devre dışı bırakın.
4. IKE versiyonunu seçin.
5. Kriptolama algoritmasını seçin.
6. Pseudo random functionu seçin.
7. Kimlik doğrulama metodu seçin.
8. Ön paylaşım anahtarını girin veya belirleyin.
9. Anahtar yenileme süresini ayarlayın.

## Alanlar

- `Göster/Gizle` (Panel): Listeyi göster veya gizlemek için seçeneği değiştirin.
- `Sayfa Başı Kayıt Sayısı` (Panel): Sayfada görüntülenecek kayıtların sayısı.
- `Profil Adı` (Genel): Profilin adını girin.
- `Durum Aktif` (Genel): Profili aktif hale getirin veya devre dışı bırakın.
- `IKE Versiyonu` (Faz 1): IKE versiyonunu seçin (IKEv1 veya IKEv2).
- `Kriptolama Algoritması` (Faz 1): Kriptolama algoritmasını seçin.
- `Pseudo Random Function` (Faz 1): Pseudo random functionu seçin.
- `DH Grubu` (Faz 1): Diffie-Hellman grubunu seçin.
- `Kimlik Doğrulama Metodu` (Faz 1): Kimlik doğrulama metodu seçin (Ön paylaşım anahtarı veya X.509 sertifikası).
- `Ön Paylaşım Anahtar` (Faz 1): Ön paylaşım anahtarını girin.
- `Anahtar Yenileme Süresi` (Faz 1): Anahtar yenileme süresini ayarlayın (saniye cinsinden).
- `Kriptolama Algoritması` (Faz 2): IPSec tünelinde kullanılan şifreleme algoritmasını seçin.
- `Pseudo Random Function` (Faz 2): Anahtar oluşturmak için bir pseudo-random fonksiyonu seçin.
- `Anahtar Yenileme Süresi` (Faz 2): Saniye cinsinden anahtar yenileme periyodunu ayarlayın.
- `Ölü Bağlantı Saptama Süresi` (Ölü Bağlantı Saptama): Saniye cinsinden ölü akran tespiti için süreyi ayarlayın.

## Görünür kontroller

- `Yenile`: Listeyi yenileyin.
- `+ Ekle`: Yeni bir profil ekleyin.

## Uyarılar

- Faz 2 için daha fazla bilgi ve ayarlar gerekebilir.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/vpn-yonetimi/ipsec-vpn-profilleri/
- Güven puanı: 1.00
