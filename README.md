# istago yakıt fiyatları

istago uygulaması akaryakıt fiyatlarını bu depodaki `yakit-fiyatlari.json` dosyasından okur:

https://omercanbalaban.github.io/istago-fiyatlar/yakit-fiyatlari.json

## Fiyat nasıl güncellenir?

### Otomatik (varsayılan)

GitHub Actions `guncelle.py`'yi **3 saatte bir** kendiliğinden çalıştırır
(`.github/workflows/fiyat-guncelle.yml`). Fiyat değiştiyse dosyayı günceller ve yayına alır;
değişmediyse günde bir kez dosyadaki `sonKontrol` alanına "fiyat değişmedi" yazar.
Bir şey yapmanız gerekmez.

- %15'ten büyük değişim olursa ya da kaynak sayfa okunamazsa iş durur ve GitHub size e-posta atar.
  Fiyatları kontrol edin; doğruysa aşağıdaki komutu `--zorla` ile çalıştırın.
- Hemen güncellemek için: GitHub'da **Actions → Fiyat güncelle → Run workflow**.
- GitHub, 60 gün hiç commit olmayan depolarda zamanlanmış işleri durdurur. Günlük `sonKontrol`
  commit'i bunu önler; yine de durursa Actions sekmesinden yeniden etkinleştirin.


### Tek komutla (81 il ve ilçeleri)

Bu klasörde Terminal'i açıp:

```bash
python3 guncelle.py --gonder
```

Betik dağıtıcının il ve ilçe bazlı fiyat listesini (KDV dahil) indirir, 81 ilin benzin, motorin ve LPG
fiyatlarını dosyaya yazar, neyin değiştiğini gösterir ve GitHub'a gönderir. Ek kurulum gerekmez.

İlçelerin çoğu il fiyatıyla aynıdır; dosyaya yalnızca il fiyatından farklı olan ilçeler yazılır
(ör. İstanbul Anadolu yakası, Gökçeada, Fethiye). Uygulama ilçe yoksa il fiyatını kullanır.

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
