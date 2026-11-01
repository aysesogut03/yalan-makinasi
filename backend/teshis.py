from kayit_okuyucu import (
    CanliOkuyucu, canli_mi, en_guncel_oturum, csv_oku,
    nabiz_tahmini, solunum_tahmini, sayi,
)

klasor = en_guncel_oturum()
print("Klasör:", klasor, "| canlı mı:", canli_mi(klasor))

olcum = csv_oku(klasor / "olcumler.csv")
atim = csv_oku(klasor / "atimlar.csv")
print("Ölçüm satırı:", len(olcum), "| Atım satırı:", len(atim))

if olcum:
    print("Sütunlar:", list(olcum[0].keys()))
    az = [v for v in (sayi(r.get("az_g")) for r in olcum) if v is not None]
    if az:
        print("az_g min/maks:", min(az), max(az))
    t0, t1 = sayi(olcum[0].get("t")), sayi(olcum[-1].get("t"))
    if t0 is not None and t1 is not None:
        print("Süre (sn):", round(t1 - t0, 1))

o = CanliOkuyucu(klasor, oynat=True)
for i in range(40):
    o.ilerle()
    if i % 5 == 0:
        print(i, "nabız:", nabiz_tahmini(list(o._atimlar), o._son_t),
              "solunum:", solunum_tahmini(list(o._az)), "nokta:", o.nokta())