# Ağ Geçidi İzleme

## Kapsam

Antikor’da var olan WAN arayüzleri için kullanıcılar ICMP Durum Takibi ve Ağ Geçidini Kapalı Olarak İşaretle opsiyonel olarak kullanılabilmektedir.

## Kullanım adımları

1. ICMP Durum Takibi seçeneğini aktif olarak ayarlayın.
2. İzlenecek IP Adresi alanına 10.2.1.253 girin.
3. Ağ Geçidini Kapalı Olarak İşaretle seçeneğini pasif olarak ayarlayın.
4. Maksimum Paket Gecikmesi (ms) alanını doldurun.
5. Maksimum Paket Kaybı (%) alanına 10 girin.
6. İzleme Sıklığı (saniye) alanına 1 girin.
7. Paket Kaybı Zaman Aşımı (saniye) alanına 2 girin.
8. Kaydet butonuna tıklayın.

## Alanlar

- `Arayüz` (Arayüz sütunu): Ağ geçidi izleme ayarları için kullanılan arayüz adı
- `Ethernet` (Ethernet sütunu): Ağ geçidi izleme ayarları için kullanılan Ethernet portu
- `Ağ Geçidi` (Ağ Geçidi sütunu): Ağ geçidi izleme ayarları için kullanılan ağ geçidi adresi
- `ICMP Durum Takibi` (ICMP Durum Takibi sütunu): Ağ geçidi izleme ayarları için ICMP durumu takibi
- `İzlenecek IP Adresi` (İzlenecek IP Adresi sütunu): Ağ geçidi izleme ayarları için izlenecek IP adresi
- `Ağ Geçidini Kapalı Olarak İşaretle` (Ağ Geçidini Kapalı Olarak İşaretle sütunu): Ağ geçidi izleme ayarları için ağ geçidini kapalı olarak işaretlemek
- `Maksimum Paket Gecikmesi (ms)` (Maksimum Paket Gecikmesi sütunu): Ağ geçidi izleme ayarları için maksimum paket gecikmesi
- `Maksimum Paket Kaybı (%)` (Maksimum Paket Kaybı sütunu): Ağ geçidi izleme ayarları için maksimum paket kaybı
- `İzleme Sıklığı (saniye)` (İzleme Sıklığı sütunu): Ağ geçidi izleme ayarları için izleme sıklığı
- `Paket Kaybı Zaman Aşımı (saniye)` (Paket Kaybı Zaman Aşımı sütunu): Ağ geçidi izleme ayarları için paket kaybı zaman aşımı
- `Durum` (Durum sütunu): Ağ geçidi izleme ayarları için durum bilgisi
- `Gecikme (ms)` (Gecikme sütunu): Ağ geçidi izleme ayarları için paket gecikmesi
- `Paket Kaybı (%)` (Paket Kaybı sütunu): Ağ geçidi izleme ayarları için paket kaybı
- `İşlemler` (İşlemler sütunu): Ağ geçidi izleme ayarları için işlemler

## Görünür kontroller

- `Yenile`: Ağ geçidi izleme listesini yeniden yükleme
- `Düzenle`: Ayarları düzenleyin
- `ICMP Durum Takibi`: Aktif/Pasif
- `İptal`: İptal
- `Kaydet`: Kaydet

## Uyarılar

- Ağ Geçidi İzleme ayarlarında izlenecek ağ geçidi adresi için; Maksimum paket gecikmesi (ms), maksimum paket kaybı (%), izleme sıklığı (saniye) ve paket kaybı zaman aşımı (saniye) cinsinden değerler kullanıcı tarafından belirlenebilmektedir, ve bu maksimum değerler aşıldığı zaman bildirim olarak düşebilmektedir.
- Maksimum Paket Gecikmesi (ms) alanının değeri belirtilmemiş.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/ag-yapilandirmasi/ag-gecidi-izleme/
- Güven puanı: 1.00
