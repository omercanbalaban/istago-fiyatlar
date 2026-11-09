# istago yakıt fiyatları

istago uygulaması akaryakıt fiyatlarını bu depodaki `yakit-fiyatlari.json` dosyasından okur:

https://omercanbalaban.github.io/istago-fiyatlar/yakit-fiyatlari.json

## Fiyat nasıl güncellenir?

1. GitHub'da `yakit-fiyatlari.json` dosyasını açın, sağ üstteki kalem simgesine basın.
2. Fiyatları değiştirin, `guncellenme` alanına tarihi yazın.
3. **Commit changes** ile kaydedin.

Yeni fiyat birkaç dakika içinde yayına girer; uygulama en geç 3 saat içinde alır. Uygulama sürümü gerekmez.

## Kurallar

- `turkiyeGeneli` yeterlidir. `iller` ve `ilceler` isteğe bağlıdır.
- Bir seviyede yazılmayan fiyat üst seviyeden alınır: ilçe → il → Türkiye geneli.
- Alanlar: `benzin` (95 oktan), `motorin`, `lpg` — ₺/litre, ondalık ayırıcı **nokta** (45.10).
- İl/ilçe adı Türkçe karakterli ya da karaktersiz yazılabilir ("İstanbul" = "ISTANBUL").
- Dosya geçerli JSON olmalı: son öğeden sonra virgül koymayın. Bozuk dosyada uygulama son bildiği fiyatı kullanmaya devam eder.
- `not`, `guncellenme` gibi tanınmayan alanlar uygulama tarafından yok sayılır.
