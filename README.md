# istago yakıt fiyatları

istago uygulaması akaryakıt fiyatlarını bu depodaki `yakit-fiyatlari.json` dosyasından okur:

https://omercanbalaban.github.io/istago-fiyatlar/yakit-fiyatlari.json

## Fiyat nasıl güncellenir?

### Tek komutla (81 il)

Bu klasörde Terminal'i açıp:

```bash
python3 guncelle.py --gonder
```

Betik Petrol Ofisi'nin il bazlı fiyat listesini (KDV dahil) indirir, 81 ilin benzin, motorin ve LPG
fiyatlarını dosyaya yazar, neyin değiştiğini gösterir ve GitHub'a gönderir. Ek kurulum gerekmez.

- Sadece görmek için `python3 guncelle.py` çalıştırın: dosya yenilenir ama gönderilmez.
- Bir ilde bir fiyat yayındakine göre **%15'ten fazla** değişmişse gönderim durur. Rakamlar doğruysa
  `python3 guncelle.py --gonder --zorla` ile gönderin.
- Sayfa yapısı değişirse, bir il eksik çıkarsa ya da fiyat mantıksız görünürse betik hata verir ve
  dosyaya dokunmaz. O durumda fiyatları elle güncelleyin.

### Elle

1. GitHub'da `yakit-fiyatlari.json` dosyasını açın, sağ üstteki kalem simgesine basın.
2. Fiyatları değiştirin, `guncellenme` alanına tarihi yazın.
3. **Commit changes** ile kaydedin.

Her iki yolda da yeni fiyat birkaç dakika içinde yayına girer (GitHub en fazla 10 dakika önbellekte
tutar); uygulama en geç 3 saat içinde alır. Uygulama sürümü gerekmez.

## Kurallar

- `turkiyeGeneli` yeterlidir. `iller` ve `ilceler` isteğe bağlıdır.
- Bir seviyede yazılmayan fiyat üst seviyeden alınır: ilçe → il → Türkiye geneli.
- Alanlar: `benzin` (95 oktan), `motorin`, `lpg` — ₺/litre, ondalık ayırıcı **nokta** (45.10).
- İl/ilçe adı Türkçe karakterli ya da karaktersiz yazılabilir ("İstanbul" = "ISTANBUL").
- Dosya geçerli JSON olmalı: son öğeden sonra virgül koymayın. Bozuk dosyada uygulama son bildiği fiyatı kullanmaya devam eder.
- `not`, `guncellenme` gibi tanınmayan alanlar uygulama tarafından yok sayılır.
