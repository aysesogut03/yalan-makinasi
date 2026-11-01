from kayit_okuyucu import en_guncel_oturum, csv_oku, sayi, solunum_tahmini

klasor = en_guncel_oturum()
olcum = csv_oku(klasor / "olcumler.csv")
zaman = [sayi(r.get("t")) for r in olcum]
print("Klasör:", klasor.name, "| satır:", len(olcum))

for eksen in ["ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps"]:
    cift = [(t, sayi(r.get(eksen))) for t, r in zip(zaman, olcum)]
    cift = [(t, v) for t, v in cift if t is not None and v is not None]
    if not cift:
        print(eksen, "veri yok")
        continue
    v = [x for _, x in cift]
    ort = sum(v) / len(v)
    sd = (sum((x - ort) ** 2 for x in v) / len(v)) ** 0.5
    print(f"{eksen}: min {min(v):.4f} maks {max(v):.4f} sd {sd:.5f} solunum {solunum_tahmini(cift[-2000:])}")