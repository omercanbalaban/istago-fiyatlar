#!/usr/bin/env python3
"""yakit-fiyatlari.json dosyasını Petrol Ofisi'nin il bazlı fiyat listesinden yeniler.

Kullanım (bu klasörün içinde):
    python3 guncelle.py            Fiyatları indirir, dosyayı yeniler, değişenleri gösterir.
    python3 guncelle.py --gonder   Ayrıca commit'leyip GitHub'a gönderir (yayına alır).
    python3 guncelle.py --gonder --zorla
                                   %15'ten büyük fiyat değişimi olsa da gönderir.

Yalnızca Python'un kendi kütüphanelerini kullanır; ek kurulum gerekmez.
"""

import argparse
import datetime
import json
import re
import statistics
import subprocess
import sys
import urllib.request
from pathlib import Path

KAYNAK_URL = "https://www.petrolofisi.com.tr/akaryakit-fiyatlari"
DOSYA = Path(__file__).resolve().parent / "yakit-fiyatlari.json"
YAKITLAR = ("benzin", "motorin", "lpg")
BUYUK_DEGISIM = 0.15  # bir ilde bir fiyat bu orandan fazla değişirse gönderim durdurulur

ILLER = """Adana Adıyaman Afyonkarahisar Ağrı Aksaray Amasya Ankara Antalya Ardahan Artvin Aydın Balıkesir
Bartın Batman Bayburt Bilecik Bingöl Bitlis Bolu Burdur Bursa Çanakkale Çankırı Çorum Denizli Diyarbakır
Düzce Edirne Elazığ Erzincan Erzurum Eskişehir Gaziantep Giresun Gümüşhane Hakkari Hatay Iğdır Isparta
İstanbul İzmir Kahramanmaraş Karabük Karaman Kars Kastamonu Kayseri Kilis Kırıkkale Kırklareli Kırşehir
Kocaeli Konya Kütahya Malatya Manisa Mardin Mersin Muğla Muş Nevşehir Niğde Ordu Osmaniye Rize Sakarya
Samsun Şanlıurfa Siirt Sinop Sivas Şırnak Tekirdağ Tokat Trabzon Tunceli Uşak Van Yalova Yozgat Zonguldak""".split()

# İstanbul'da il fiyatı Avrupa yakasınınkidir; bu ilçeler Anadolu yakası fiyatını alır.
ANADOLU_ILCELERI = ["Adalar", "Ataşehir", "Beykoz", "Çekmeköy", "Kadıköy", "Kartal", "Maltepe", "Pendik",
                    "Sancaktepe", "Sultanbeyli", "Şile", "Tuzla", "Ümraniye", "Üsküdar"]

# Kaynakta farklı yazılabilecek il adları
TAKMA_ADLAR = {"AFYON": "Afyonkarahisar", "KMARAS": "Kahramanmaraş", "ICEL": "Mersin", "URFA": "Şanlıurfa"}


class Hata(Exception):
    pass


def sadelestir(metin):
    """'Kırşehir' -> 'KIRSEHIR' (uygulamadaki TurkishText ile aynı mantık)."""
    metin = metin.replace("i", "İ").replace("ı", "I").upper()
    for tr, en in zip("İŞĞÜÖÇ", "ISGUOC"):
        metin = metin.replace(tr, en)
    return re.sub(r"[^A-Z]", "", metin)


def sayfayi_indir():
    istek = urllib.request.Request(KAYNAK_URL, headers={"User-Agent": "Mozilla/5.0 (istago fiyat guncelleme)"})
    with urllib.request.urlopen(istek, timeout=30) as yanit:
        return yanit.read().decode("utf-8")


def fiyat(hucre):
    eslesme = re.search(r'class="with-tax">\s*([\d.,]+)\s*<', hucre)
    if not eslesme:
        return None
    deger = float(eslesme.group(1).replace(",", "."))
    return round(deger, 2) if deger > 0 else None


def tabloyu_oku(html):
    """{il: {yakıt: fiyat}} ve İstanbul'un iki yakasını döndürür."""
    baslangic = html.find("table-with-tax")
    if baslangic < 0:
        raise Hata("Fiyat tablosu bulunamadı; Petrol Ofisi sayfa yapısını değiştirmiş olabilir.")
    tablo = html[baslangic:html.find("</table>", baslangic)]

    basliklar = [re.sub(r"<[^>]+>", "", b).strip() for b in re.findall(r"<th[^>]*>(.*?)</th>", tablo, re.S)]
    beklenen = {1: "Kurşunsuz 95", 2: "Diesel", 6: "Otogaz"}
    for sira, parca in beklenen.items():
        if len(basliklar) <= sira or parca not in basliklar[sira]:
            raise Hata(f"Tablo sütunları değişmiş (beklenen '{parca}', bulunan: {basliklar}).")

    by_fold = {sadelestir(il): il for il in ILLER}
    iller, istanbul, taninmayan = {}, {}, []
    for satir in re.findall(r"<tr[^>]*>(.*?)</tr>", tablo, re.S):
        hucreler = re.findall(r"<td[^>]*>(.*?)</td>", satir, re.S)
        if len(hucreler) < 7:
            continue
        ad = re.sub(r"<[^>]+>", "", hucreler[0]).strip()
        fiyatlar = {"benzin": fiyat(hucreler[1]), "motorin": fiyat(hucreler[2]), "lpg": fiyat(hucreler[6])}
        fiyatlar = {k: v for k, v in fiyatlar.items() if v is not None}
        anahtar = sadelestir(ad)
        if anahtar.startswith("ISTANBUL"):
            istanbul["ANADOLU" if "ANADOLU" in anahtar else "AVRUPA"] = fiyatlar
            continue
        il = by_fold.get(anahtar) or TAKMA_ADLAR.get(anahtar)
        if il:
            iller[il] = fiyatlar
        else:
            taninmayan.append(ad)

    if set(istanbul) != {"AVRUPA", "ANADOLU"}:
        raise Hata("İstanbul Avrupa/Anadolu satırları bulunamadı.")
    iller["İstanbul"] = istanbul["AVRUPA"]

    eksik = [il for il in ILLER if il not in iller]
    if eksik or taninmayan:
        raise Hata(f"İller eşleşmedi. Eksik: {eksik}  Tanınmayan: {taninmayan}")
    for il, f in list(iller.items()) + [("İstanbul Anadolu", istanbul["ANADOLU"])]:
        for yakit in ("benzin", "motorin"):
            if yakit not in f:
                raise Hata(f"{il} için {yakit} fiyatı yok.")
        for yakit, deger in f.items():
            if not 10 <= deger <= 1000:
                raise Hata(f"{il} {yakit} fiyatı mantıksız görünüyor: {deger}")
    return iller, istanbul["ANADOLU"]


def obje(f):
    return "{ " + ", ".join(f'"{k}": {f[k]:.2f}' for k in YAKITLAR if k in f) + " }"


def json_yaz(iller, anadolu):
    genel = {}
    for yakit in YAKITLAR:
        degerler = [f[yakit] for f in iller.values() if yakit in f]
        if degerler:
            genel[yakit] = round(statistics.median(degerler), 2)

    simdi = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    satirlar = [
        "{",
        '  "not": "KDV dahil pompa fiyatları (₺/L). İstanbul il fiyatı Avrupa yakası; Anadolu yakası ilçeleri ayrı yazıldı. '
        'turkiyeGeneli = 81 ilin medyanı, sadece il bulunamazsa kullanılır. Bu dosya guncelle.py ile üretilir.",',
        f'  "kaynak": "Petrol Ofisi il bazlı fiyat listesi ({KAYNAK_URL.split("//")[1].removeprefix("www.")})",',
        f'  "guncellenme": "{simdi}",',
        f'  "turkiyeGeneli": {obje(genel)},',
        '  "iller": {',
    ]
    sirali = sorted(iller, key=sadelestir)
    for i, il in enumerate(sirali):
        virgul = "," if i < len(sirali) - 1 else ""
        if il == "İstanbul":
            satirlar.append('    "İstanbul": {')
            satirlar += [f'      "{k}": {iller[il][k]:.2f},' for k in YAKITLAR if k in iller[il]]
            satirlar.append('      "ilceler": {')
            for j, ilce in enumerate(ANADOLU_ILCELERI):
                satirlar.append(f'        "{ilce}": {obje(anadolu)}' + ("," if j < len(ANADOLU_ILCELERI) - 1 else ""))
            satirlar += ["      }", "    }" + virgul]
        else:
            satirlar.append(f'    "{il}": {obje(iller[il])}{virgul}')
    satirlar += ["  }", "}", ""]
    metin = "\n".join(satirlar)
    json.loads(metin)  # geçerli JSON olduğundan emin ol
    return metin, genel


def yayindaki_metin():
    """Son commit'teki (yayındaki) dosya; git yoksa diskteki dosya."""
    try:
        return git("show", f"HEAD:{DOSYA.name}")
    except Hata:
        return DOSYA.read_text(encoding="utf-8") if DOSYA.exists() else None


def eski_fiyatlar(metin):
    """Dosya metnindeki il fiyatlarını (İstanbul Anadolu dahil) okur."""
    if not metin:
        return {}, None
    veri = json.loads(metin)
    sonuc = {}
    for il, kayit in veri.get("iller", {}).items():
        sonuc[il] = {k: kayit[k] for k in YAKITLAR if k in kayit}
        ilceler = kayit.get("ilceler") or {}
        if ilceler:
            ilk = next(iter(ilceler.values()))
            sonuc[f"{il} (ilçeler)"] = {k: ilk[k] for k in YAKITLAR if k in ilk}
    return sonuc, veri.get("turkiyeGeneli")


def git(*args):
    sonuc = subprocess.run(["git", *args], cwd=DOSYA.parent, capture_output=True, text=True)
    if sonuc.returncode != 0:
        raise Hata(f"git {' '.join(args)} başarısız:\n{sonuc.stderr.strip()}")
    return sonuc.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description="yakit-fiyatlari.json dosyasını yeniler.")
    ap.add_argument("--gonder", action="store_true", help="commit'leyip GitHub'a gönder")
    ap.add_argument("--zorla", action="store_true", help="büyük fiyat değişiminde de gönder")
    ap.add_argument("--html", help="(test için) sayfayı indirmek yerine bu dosyadan oku")
    args = ap.parse_args()

    if args.gonder:
        git("pull", "--ff-only", "-q")

    html = Path(args.html).read_text(encoding="utf-8") if args.html else sayfayi_indir()
    iller, anadolu = tabloyu_oku(html)
    # Karşılaştırma her zaman yayındaki sürümle yapılır; önizlemede yazılmış ama
    # gönderilmemiş bir dosya, sonraki --gonder'i ve büyük değişim kontrolünü atlatamaz.
    eski, eski_genel = eski_fiyatlar(yayindaki_metin())
    metin, genel = json_yaz(iller, anadolu)

    yeni = dict(iller)
    yeni["İstanbul (ilçeler)"] = anadolu
    degisen, buyuk = [], []
    for il, f in yeni.items():
        onceki = eski.get(il, {})
        for yakit, deger in f.items():
            eski_deger = onceki.get(yakit)
            if eski_deger != deger:
                degisen.append((il, yakit, eski_deger, deger))
                if eski_deger and abs(deger - eski_deger) / eski_deger > BUYUK_DEGISIM:
                    buyuk.append(f"{il} {yakit}: {eski_deger:.2f} -> {deger:.2f}")

    if not degisen:
        print("Fiyatlar yayındakiyle aynı; dosyaya dokunulmadı.")
        return 0

    illerde = sorted({d[0] for d in degisen})
    print(f"{len(illerde)} ilde {len(degisen)} fiyat değişti.")
    for yakit in YAKITLAR:
        once = (eski_genel or {}).get(yakit)
        print(f"  Türkiye geneli {yakit:8}: {once if once is not None else '-'} -> {genel.get(yakit, '-')}")
    for il, yakit, once, sonra in degisen[:8]:
        print(f"  {il} {yakit}: {once if once is not None else '-'} -> {sonra:.2f}")
    if len(degisen) > 8:
        print(f"  ... ve {len(degisen) - 8} değişiklik daha")

    if buyuk:
        print(f"\nDİKKAT: %{int(BUYUK_DEGISIM * 100)}'ten büyük değişim var:")
        for satir in buyuk[:10]:
            print("  " + satir)

    if args.gonder and buyuk and not args.zorla:
        print("\nBüyük değişim olduğu için gönderilmedi, dosyaya da dokunulmadı.")
        print("Kontrol edip doğruysa: python3 guncelle.py --gonder --zorla")
        return 1

    DOSYA.write_text(metin, encoding="utf-8")
    if not args.gonder:
        print("\nDosya yenilendi ama yayına alınmadı. Yayına almak için: python3 guncelle.py --gonder")
        return 0

    git("add", DOSYA.name)
    git("commit", "-q", "-m", f"Fiyatlar {datetime.date.today().isoformat()}: {len(illerde)} ilde değişiklik")
    git("push", "-q")
    print("\nGitHub'a gönderildi. Birkaç dakika içinde yayında olur; uygulama en geç 3 saat içinde alır.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Hata as hata:
        print(f"HATA: {hata}\nDosya değiştirilmedi.", file=sys.stderr)
        sys.exit(2)
    except OSError as hata:
        print(f"HATA: Bağlantı/dosya sorunu: {hata}\nDosya değiştirilmedi.", file=sys.stderr)
        sys.exit(2)
