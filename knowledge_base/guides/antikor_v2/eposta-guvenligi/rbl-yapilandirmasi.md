# RBL Yapılandırması

## Kapsam

Gerçek zamanlı  Karadelik Listesi (Real Time Blackhole List)spam gönderimi yaptığı tespit edilen IP adresleri tutulmaktadır. Mail sunucuları gelen mailleri kontrol ederek göndericinin kara listede bulunması durumunda maili reddeder. Antikor NGFW’de 18 adet RBL sunucusundan çekilen kara listeler kullanılabilmektedir.

## Kullanım adımları

1. Gönderici adreslerini ve HELO/EHLO alan adının kontrolü sağlayın.

## Alanlar

- `RBL Sunucu Adı` (RBL Sunucu Adı): RBL sunucusunun adını seçer.
- `Sunucu Adresi` (Sunucu Adresi): Sunucu adresini girer.
- `Kullan` (Kullan): RBL sunucusunu kullanır.

## Görünür kontroller

- `RBL Denetimi`: RBL denetimini etkinleştirir veya devre dışı bırakır.
- `Gönderici Adresleri Kontrol Et`: Gönderici adreslerini kontrol eder.
- `HELO/EHLO Alan Adını Kontrol Et`: HELO/EHLO alan adını kontrol eder.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/eposta-guvenligi/rbl-yapilandirmasi/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
