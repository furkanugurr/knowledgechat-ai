# Antispam Ayarları

## Kapsam

Eşik puan ve gri liste ayarlarının yanı sıra; antivirüs kontrolü, SMTP FROM için MX Kontrolü, SPF Kontrolü, DKIM Kontrolü, DMARC Kontrolü, Oltalama Kontrolü buradan ayarlanmaktadır.

## Kullanım adımları

1. Gri Liste Eşik Puanı ayarlamak için 'Gri Liste Eşik Puanı' alanına değer girin.
2. Spam Başlığı Ekleme Eşik Puanı ayarlamak için 'Spam Başlığı Ekleme Eşik Puanı' alanına değer girin.
3. Kesin Spam Eşik Puanı ayarlamak için 'Kesin Spam Eşik Puanı' alanına değer girin.
4. DKIM kontrolünü etkinleştirmek için 'DKIM Kontrolü Aktif' butonuna tıklayın.
5. DMARC kontrolünü etkinleştirmek için 'DMARC Kontrolü Aktif' butonuna tıklayın.

## Alanlar

- `Gri Liste Eşik Puanı` (Eşik Puan Ayarları): Gri liste eşik puanı değeri.
- `Spam Başlığı Ekleme Eşik Puanı` (Eşik Puan Ayarları): Spam başlığı ekleme eşik puanı değeri.
- `Kesin Spam Eşik Puanı` (Eşik Puan Ayarları): Kesin spam eşik puanı değeri.
- `DKIM Kontrolü` (DKIM Kontrolü): DKIM kontrolünün durumunu gösterir (aktif/passive).
- `DMARC Kontrolü` (DMARC Kontrolü): DMARC kontrolünün durumunu gösterir (aktif/passive).

## Görünür kontroller

- `Ekle`: Beyaz listeye yeni bir öğe ekleme seçeneği.
- `Yenile`: Beyaz listeyi güncellemek için kullanılan buton.
- `Sil`: Önceden eklendiği beyaz listeden bir öğe silmek için kullanılan buton.
- `Düzenle`: Önceden eklendiği beyaz listedeki bir öğeyi düzenlemek için kullanılan buton.
- `DKIM Kontrolü Aktif`: DKIM kontrolünü etkinleştirmek için.
- `DMARC Kontrolü Aktif`: DMARC kontrolünü etkinleştirmek için.
- `Beyaz Liste Yenile`: Beyaz listeyi güncellemek için.
- `Beyaz Liste Ekle`: Beyaz listeye yeni alan adı eklemek için.
- `Gri Liste Ayarları Aktif`: Gri listeyi etkinleştirmek için.
- `Oltalama Kontrolü Aktif`: Oltalama kontrolünü etkinleştirmek için.

## Uyarılar

- Eğer kuralın çalışmaması halinde belirlenen puan artmaktadır. Belirlenen eşik puanları (gri liste eşik puanı, spam başlığı ekleme eşik puanı, e-posta konusu değiştirme eşik puanı ve kesin spam - reddetme eşik puanı) geçildiği takdirde engellenmektedir.
- E-posta Konusu Değiştirme Eşik Puanı alanının değeri boş.
- SMTP FROM için MX Kontrolü, SPF Kontrolü, DKIM Kontrolü, DMARC Kontrolü ve Oltalama Kontrolü bölümlerinin detayları görüntülenmemiştir.
- Beyaz listeye eklenen alan adları ve diğer detaylı ayarlar hakkında daha fazla bilgi almak için 'Düzenle' butonunu kullanabilirsiniz.
- Gri liste ayarlarını etkinleştirmek için 'Gri Liste Ayarları Aktif' butonuna tıklayın.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/eposta-guvenligi/antispam-ayarlari/
- Güven puanı: 1.00
- Durum: Otomatik kalite kapısından geçmiş taslak; indekslenmemiştir.
