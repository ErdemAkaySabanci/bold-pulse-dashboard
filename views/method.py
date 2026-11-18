import pandas as pd
import streamlit as st

from src import config, insights
from src import metrics as M
from src.data import load
from src.ui import components as C, fmt
from src.ui.theme import tok

t = tok()
q = load.quality()
R = load.ratings()
rv = load.reviews()
when = load.collected_at()
val = load.validation()
validated = val is not None and len(val) > 0

C.hero(
    "Metodoloji",
    "Bu dashboard nasıl hazırlandı?",
    "Her sayı, sayfa açıldığında herkese açık mağaza verisinden yeniden hesaplanır. Bu sayfa "
    "verinin nereden geldiğini, nasıl temizlendiğini ve neyi söyleyemeyeceğini anlatır.",
)

C.section("Veri hattı", "Toplamadan sunuma beş adım.", icon="🛠️", color=t["blue"])
steps = [
    ("01 · TOPLA", "Mağazalar", "Google Play'de 74 dil, App Store'da değerlendirmesi olan tüm ülkeler; "
     "iki mağazada 175'er ülkenin değerlendirmeleri.", t["blue"], True),
    ("02 · TEMİZLE", "Düzenle", "Tekrarları ayıkla, tarihleri UTC'ye çevir, çok kısa yorumları "
     "işaretle, kalite raporu üret.", t["green"], True),
    ("03 · ÇEVİR & ETİKETLE", "Yapay zekâ", "Gemini (ücretsiz sürüm) yorumun gerçek dilini tespit "
     "edip İngilizceye çevirir; çeviriler elle kontrol edilir. Konu etiketleri sonraki adım.",
     t["purple"], load.has_translations()),
    ("04 · DOĞRULA", "İnsan kontrolü", "50 yorum Gemini'yi görmeden elle etiketlendi (kör test); "
     "uyum aşağıda. Örneklemdeki yorumlarda nihai etiket insanınki.",
     t["orange"], validated),
    ("05 · SUN", "Bu uygulama", "Streamlit + Plotly; hesaplamalar test edilmiş ayrı bir Python "
     "modülünde.", t["red"], True),
]
st.markdown('<div class="p-steps">' + "".join(
    f'<div class="p-card p-step" style="--c:{c}"><div class="k">{k}{"" if done else " · BEKLİYOR"}</div>'
    f'<div class="t">{ti}</div><div class="d">{d}</div></div>'
    for k, ti, d, c, done in steps) + "</div>", unsafe_allow_html=True)

C.section("Kaynaklar", f"Veri tarihi: {fmt.date_long(when) if when is not None else '—'}.",
          icon="📦", color=t["orange"])
as_local = R[(R["store"] == "app_store") & (R["scope"] == "local")]
tr_note = "—"
if load.has_translations():
    _tr = pd.read_csv(config.TRANSLATIONS_CSV, keep_default_na=False, dtype=str)
    _done = _tr[_tr["text_en"].str.strip() != ""]
    tr_note = (f"Makine çevirisi ({', '.join(sorted(_tr['model'].unique()))}); "
               f"{int(_done['reviewed'].eq('True').sum())} çevirinin hepsi orijinaliyle karşılaştırıldı, "
               f"{int(_done.get('edited', pd.Series(dtype=str)).eq('True').sum())} tanesi elle düzeltildi")
gp_scope = R[R["store"] == "google_play"]["scope"].value_counts()
src = pd.DataFrame([
    {"Kaynak": "App Store değerlendirmeleri (iTunes Lookup API)",
     "Ne veriyor": "Ülke bazında ortalama ve değerlendirme sayısı",
     "Kapsam": f"{int((R['store'] == 'app_store').sum())} ülkede yayında · {len(as_local)} ülkede değerlendirme · "
               f"{fmt.num(as_local['rating_count'].sum())} değerlendirme",
     "Eksik": "Yıldız dağılımı"},
    {"Kaynak": "Google Play değerlendirmeleri (mağaza sayfası)",
     "Ne veriyor": "Dünya geneli sayı, ortalama ve yıldız dağılımı; ülke ortalaması",
     "Kapsam": f"{int(gp_scope.get('local', 0))} ülkede yerel değer · "
               f"{int(gp_scope.get('global_fallback', 0))} ülkede dünya geneli · "
               f"{int(gp_scope.get('none', 0))} ülkede veri yok",
     "Eksik": "Ülke bazında değerlendirme sayısı"},
    {"Kaynak": "App Store yorumları (RSS)",
     "Ne veriyor": "Metin, yıldız, sürüm, ülke",
     "Kapsam": f"{int((rv['store'] == 'app_store').sum())} yorum · "
               f"{rv.loc[rv['store'] == 'app_store', 'country'].nunique()} ülke",
     "Eksik": "Geliştirici yanıtları"},
    {"Kaynak": "İngilizce çeviriler (Gemini, ücretsiz)",
     "Ne veriyor": "Yorumun gerçek dili ve İngilizce çevirisi",
     "Kapsam": (f"{int((rv['text_en'].str.strip() != '').sum())} yorum çevrildi · "
                f"{rv.loc[rv['text_en'].str.strip() != '', 'source_lang'].nunique()} dilden")
               if load.has_translations() else "Henüz çalıştırılmadı",
     "Eksik": tr_note},
    {"Kaynak": "Google Play yorumları (google-play-scraper)",
     "Ne veriyor": "Metin, yıldız, sürüm, beğeni, geliştirici yanıtı",
     "Kapsam": f"{int((rv['store'] == 'google_play').sum())} yorum · "
               f"{rv.loc[rv['store'] == 'google_play', 'lang'].nunique()} dil",
     "Eksik": "Yorumcunun ülkesi"},
])
st.table(src.set_index("Kaynak"))

C.section("Veri kalitesi özeti", icon="🧾", color=t["green"])
dq = [
    ("Toplanan yazılı yorum", f"{q.get('clean_rows', '—')}"),
    ("Tarih aralığı", f"{fmt.date_long(rv['date'].min())} – {fmt.date_long(rv['date'].max())}"),
    ("Toplamada ayıklanan tekrar", "İlk sürümde 163 satırın 52'si Google Play'in ABD/BK kopyasıydı; "
                                  "toplayıcı artık yorumları dil + ID ile tekilleştiriyor (mevcut çekimde 0)."),
    ("Temizlikte silinen", f"{sum(s_['removed'] for s_ in q.get('cleaning_steps', []))}"),
    ("İngilizce çevrilen", f"{int((rv['text_en'].str.strip() != '').sum())} yorum, hepsi elle okundu"),
]
if load.is_classified():
    n_cl = int(rv["is_classified"].sum())
    empty = int((rv["is_classified"] & (rv["topics"] == "")).sum())
    dq.append(("Gemini ile etiketlenen", f"{n_cl} / {len(rv)} yorum · {len(rv) - n_cl} sınıflandırılamadı · "
                                         f"{empty} yorum konusuz döndü"))
_off = config.OFFICIAL_DISPLAY
_us = M.app_store_countries(R)
_us = _us[_us["country"] == "us"]
_g = R[(R["store"] == "google_play") & (R["scope"] == "global")]
if len(_us) and len(_g):
    ok1 = M.matches_display(float(_us["avg_rating"].iloc[0]), int(_us["n"].iloc[0]),
                            _off["app_store_us"]["avg"], _off["app_store_us"]["count"])
    ok2 = M.matches_display(float(_g["avg_rating"].iloc[0]), int(_g["rating_count"].iloc[0]),
                            _off["google_play"]["avg"], _off["google_play"]["count"])
    dq.append(("Resmi rakamla karşılaştırma",
               f"{'✓' if ok1 else '≠'} App Store ABD {fmt.num(float(_us['avg_rating'].iloc[0]), 2)} / "
               f"{fmt.num(int(_us['n'].iloc[0]))} → sayfada 4,8 / 1,9 B · "
               f"{'✓' if ok2 else '≠'} Google Play {fmt.num(float(_g['avg_rating'].iloc[0]), 2)} / "
               f"{fmt.num(int(_g['rating_count'].iloc[0]))} → sayfada 4,7 / 1,3 B"))
st.table(pd.DataFrame(dq, columns=["Kontrol", "Sonuç"]).set_index("Kontrol"))

C.section("Temizlik", f"{q.get('raw_rows', '—')} ham satır → {q.get('clean_rows', '—')} temiz yorum.",
          icon="🧹", color=t["green"])
if q.get("cleaning_steps"):
    names = {"drop empty text": "Boş metinleri çıkar",
             "drop duplicate review_id": "Aynı ID'li tekrarları çıkar",
             "drop duplicate store+text+rating+date": "Aynı içerikli tekrarları çıkar",
             "drop unparseable date": "Tarihi okunamayanları çıkar",
             "drop missing/invalid rating": "Yıldızı geçersiz olanları çıkar"}
    steps_df = pd.DataFrame(q["cleaning_steps"])
    steps_df["step"] = steps_df["step"].map(lambda s: names.get(s, s))
    st.dataframe(steps_df.rename(columns={"step": "Adım", "removed": "Çıkarılan", "remaining": "Kalan"}),
                 hide_index=True, width="stretch")

C.section("Sayılara nasıl güveniyoruz?", icon="📐", color=t["purple"])
st.markdown(f"""
- **Yorum tonu.** *Olumsuz* = 1–2★ · *Nötr* = 3★ · *Olumlu* = 4–5★. Ton, oyuncunun verdiği yıldızdan gelir.
- **Güven etiketleri.** *Güvenilir*: {M.STRONG_N}+ veri · *Fikir verir*: {M.DIRECTIONAL_N}–{M.STRONG_N - 1} veri
  (ve sayısı bilinmeyen tüm Google Play ülke değerleri) · *Az veri*: {M.DIRECTIONAL_N}'den az.
- **Oranlar** (ör. olumsuz, yani 1–2★ yorum payı) için Wilson güven aralığı kullanılır.
- **Ülke ortalamalarının olası aralığı:** Apple yıldızların dağılımını yayınlamadığı için, o ortalamada
  mümkün olan en geniş dağılım varsayılır (Bhatia–Davis sınırı). Bir ülke ancak bu en kötü durumda bile
  mağaza ortalamasının altındaysa kırmızıyla işaretlenir.
- **Adil sıralama:** Az değerlendirmeli ülkelerin ortalaması, sanki {M.DEFAULT_PRIOR_WEIGHT} ek değerlendirme mağaza
  ortalamasındaymış gibi ortalamaya çekilir (Bayes ortalaması).
- **Reklam bahsi:** Konu etiketleri hazır olana kadar çok dilli bir anahtar kelime listesiyle sayılır
  (reklam, ads, Werbung, publicité, anúncio…).
- Tek haneli sayılarda **yüzde yerine adet** gösterilir.
""")

C.section("Etiket doğrulama (kör test)",
          "Gemini'nin etiketleri, aynı yorumlara Gemini'yi görmeden elle verilen etiketlerle karşılaştırılır "
          "(50 yorumluk kör örneklem, sabit seed).", icon="✅", color=t["orange"])
if not validated:
    C.empty_state("Elle etiketleme bekleniyor",
                  "50 yorumluk örneklem Araçlar → Etiketleme sayfasında etiketlendiğinde konu bazında uyum "
                  "yüzdesi ve Cohen's κ burada görünecek.")
elif not load.is_classified():
    C.empty_state("Gemini etiketleri bekleniyor", "Karşılaştırma için önce <code>python -m src.classify</code>.")
else:
    # Compare against Gemini's RAW labels, not the final (human-overridden) ones.
    model_labels = rv[rv["is_classified"]][["review_id", "topics_gemini"]].rename(columns={"topics_gemini": "topics"})
    tbl, exact = M.label_agreement(val, model_labels, list(fmt.TOPIC))
    n_cmp = int(tbl["n"].iloc[0]) if len(tbl) else 0
    mean_agree = float(tbl["agreement"].mean()) if len(tbl) else float("nan")
    jj = val.merge(rv[["review_id", "churn_signal_gemini"]], on="review_id")
    churn_h = int(jj["churn_signal"].astype(str).str.lower().eq("true").sum())
    churn_g = int(jj["churn_signal_gemini"].astype(bool).sum())
    st.markdown(f"**{n_cmp}** yorum karşılaştırıldı · konu bazında ortalama uyum **{fmt.pct(mean_agree)}** · "
                f"bütün konu seti birebir aynı olan yorum payı **{fmt.pct(exact)}**.")
    show = tbl.assign(konu=tbl["topic"].map(fmt.topic))
    st.dataframe(show[["konu", "agreement", "kappa", "human_yes", "model_yes"]], hide_index=True, width="stretch",
                 column_config={"konu": "Konu",
                                "agreement": st.column_config.ProgressColumn("Uyum", format="percent", min_value=0.0, max_value=1.0),
                                "kappa": st.column_config.NumberColumn("Cohen's κ", format="%.2f",
                                    help="Şans eseri uyumdan arındırılmış uyum. 0,6+ iyi, 0,8+ çok iyi."),
                                "human_yes": st.column_config.NumberColumn("Elle: var", format="%d"),
                                "model_yes": st.column_config.NumberColumn("Gemini: var", format="%d")})
    C.takeaways(insights.label_takeaways(tbl, churn_g, churn_h))
    C.note("Konu nadir olduğunda (ör. 50 yorumda 2 kez) uyum yüzdesi yüksek görünür ama κ düşük olabilir; "
           "κ bu yüzden ayrıca verilir.")

C.section("Bilinen sınırlar", icon="⚠️", color=t["red"])
total = int(as_local["rating_count"].sum()) + int(
    R.query("store=='google_play' and scope=='global'")["rating_count"].sum())
st.markdown(f"""
1. **Yorum örneklemi küçük ve kendiliğinden seçilmiş.** {fmt.num(total)} değerlendirmeye karşılık {len(rv)} yazılı yorum var.
   Yorum yazanlar tüm oyuncuları temsil etmez.
2. **Değerlendirmelerde zaman serisi yok.** Tek bir anlık görüntü var; trend, anomali ve güncelleme etkisi
   henüz ölçülemez.
3. **Doğrulanmış sürüm tarihleri yok.** Sürüm numaraları var (sürüm başına yaklaşık 3 yorum), ama
   güncelleme etkisi analizi tahmin olurdu.
4. **Google Play coğrafyayı gizliyor.** Yorumlarda ülke yerine dil var; ülke ortalamalarında değerlendirme sayısı yok.
5. **Gösterim cihaza göre değişiyor.** Google Play web sitesi ülke ortalamasını, Google Play Games (PC)
   dünya geneli ortalamayı gösterir. İkisi de bu veriyle uyumlu.
6. **Sadece beyan edilen geri bildirim.** Davranış verisi (elde tutma, oturum, harcama) yok; PULSE
   oyuncuların ne söylediğini anlatır, ne yaptığını değil.
""")

C.section("Tasarım notu", icon="🎨", color=t["blue"])
st.markdown("""
Renkler Market Match! ikonundan alındı. Grafik renkleri açık ve koyu temada renk körlüğü, parlaklık
ve kontrast testlerinden geçirildi. Kırmızı–mavi skalası, kırmızı–yeşilin aksine renk körlüğünde de
ayırt edilir. Güven bilgisi hiçbir zaman yalnızca renkle verilmez.
""")
