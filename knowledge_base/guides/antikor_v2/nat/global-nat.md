# Global NAT

## Kapsam

Yerel ağda bulunan LAN ve VLAN’ların NAT IP Adresleri buradan belirlenmektedir. Ayrıca NAT yapılan WAN bacağının Trafiği de özellik kullanıcı tarafından aktif edildiği takdirde loglanabilmektedir.

## Kullanım adımları

1. Aktif durumu seçin.

## Alanlar

- `LAN1 - igb1 (192.168.100.0/24)` (Yerel Ağ): LAN1 için NAT IP Adresi girilmesi gereken alan.
- `LAN1.400 - igb1.400 (192.168.140.0/24)` (Yerel Ağ): LAN1.400 için NAT IP Adresi girilmesi gereken alan.
- `LAN2 - igb2 (1.1.1.0/24)` (Yerel Ağ): LAN2 için NAT IP Adresi girilmesi gereken alan.
- `LAN3 - igb3 (192.168.1.0/24)` (Yerel Ağ): LAN3 için NAT IP Adresi girilmesi gereken alan.

## Görünür kontroller

- `Aktif`: WAN1 NAT Durumu için aktif durumunu belirler.
- `Pasif`: WAN1 NAT Durumu için pasif durumunu belirler.

## Kaynak bilgisi

- Sayfa: https://kitaplik.epati.com.tr/kilavuzlar/antikor-v2-yeni-nesil-guvenlik-duvari/nat-yapilandirmasi/global-nat/
- Güven puanı: 0.94
