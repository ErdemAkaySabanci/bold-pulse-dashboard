"""Benim Ürün Önerilerim: the author's own product recommendations, written after playing the game.

Approach: not new ideas from scratch, but features proven in competing games and how each could be
integrated into Market Match!. Order on the page = order of RECS.
"""
from html import escape
from pathlib import Path

import streamlit as st

from src import insights
from src import metrics as M
from src.data import load
from src.ui import components as C

PLAYED_TO_LEVEL = 84
ASSETS = Path(__file__).resolve().parents[1] / "assets" / "recs"

C.hero(
    "Benim Ürün Önerilerim",
    "Rakiplerden öğrenip Market Match!'e uyarlamak",
    f"Market Match!'i <b>{PLAYED_TO_LEVEL}. seviyeye</b> kadar oynadım. Oyun belirli bir oyuncu kitlesine "
    "ulaştı ve yatırım aldı. Bence bu aşamada en makul yol sıfırdan fikir üretmek değil; türdeki rakiplerin "
    "işe yaradığını kanıtlamış özelliklerinden hangilerinin örnek alınabileceğini ve Market Match!'e "
    "<b>nasıl entegre edilebileceğini</b> göstermek.",
)

def sound_table(rows: list[tuple[str, str, str]]) -> str:
    """Material -> example items -> sound, as a compact HTML table inside a card row."""
    body = "".join(f"<tr><td class='n'>{k}</td><td><b>{m}</b></td><td>{ex}</td><td><span class='snd'>{sd}</span></td></tr>"
                   for k, (m, ex, sd) in enumerate(rows, start=1))
    return ("<table class='p-rtable'><thead><tr><th></th><th>Malzeme</th><th>Örnek ürünler</th><th>Eşleşmede çalan ses</th>"
            f"</tr></thead><tbody>{body}</tbody></table>")


C.data_source(f"Kendi oyun deneyimim ({PLAYED_TO_LEVEL}. seviyeye kadar) · rakip oyunlar · konsept görseller "
              "bana ait · reklam önerisinde mağaza yorumları")

# --- Evidence for the ads card, computed from the same reviews as the Overview page (no hand-typed counts)
rv = load.reviews()
n_crit = int(rv["rating_bucket"].isin(["negative", "neutral"]).sum())
ad_rv = insights.ad_mentions(rv)
n_ads = len(ad_rv)
n_noads = int(rv["monetization"].map(lambda v: "no_ads_pack" in M.split_labels(v)).sum()) if "monetization" in rv else 0
# Two short player quotes, with a Turkish rendering; skipped if the review is not in the data.
QUOTES = [("after each level an ad will start and stop",
           "309 seviye oynadım, birden her seviyeden sonra reklam açılıp takılmaya başladı."),
          ("paid for the removal of ads",
           "Reklam mı görüyorum? Reklamları kaldırmak için para ödediğime eminim.")]
quotes_html = "".join(
    f"<div style='margin:.15rem 0'>“{escape(hit['text'].iloc[0][:150])}{'…' if len(hit['text'].iloc[0]) > 150 else ''}” "
    f"<span style='opacity:.75'>({hit['rating'].iloc[0]}★ · {escape(tr)})</span></div>"
    for key, tr in QUOTES
    if len(hit := ad_rv[ad_rv["text"].str.contains(key, case=False, regex=False)]))

# One dict per recommendation. rows = (label, html) in reading order; images = (file, tag, caption, concept).
RECS: list[dict] = [
    dict(
        title="Boosterları zorunlu ve ücretsiz bir eğitimle öğret",
        rows=[
            ("Bulgu",
             "Üç booster (<b>Undo, Mixer, Scanner</b>) 2. seviyeden itibaren ekranda duruyor, mağazada paketlerle "
             "satılıyor (<b>Limited Deal 99,99 TL</b> · <b>Starter Bag 499,99 TL</b>) ve Order Journey'de "
             "kazanılıyor; ama <b>ilk 50 seviyede hiçbiri öğretilmiyor</b>. Oyuncudan, ne işe yaradığını "
             "bilmediği bir şey için para ödemesi bekleniyor."),
            ("Rakip örneği",
             "Tam bir rakip olmasa da yine bir puzzle oyunu olan <b>Manor Cafe</b>, ilk boosterını "
             "<b>11.</b>, ikincisini <b>14. seviyede</b> ücretsiz haklarla tanıtıyordu."),
            ("Öneri",
             "Her boosterı zorunlu bir eğitim ve 1 ücretsiz hakla tanıt: önce <b>Undo</b> (~10. seviye), "
             "diğer ikisi birkaç seviye arayla."),
        ],
        metrics=["İlk booster kullanımının seviyesi", "Booster paketlerinin satın alma oranı",
                 "Booster kullananlarla kullanmayanların retention farkı"],
        effort="Düşük", impact="Yüksek",
        images=[("booster-tutorial-concept.jpg", "KONSEPT", "Zorunlu Undo eğitimi mockup'ı", True)],
    ),
    dict(
        title="Ana ekrandaki marketi oyuncuyla birlikte büyüt",
        rows=[
            ("Bulgu",
             f"Ana ekranın arka planı oyun boyunca hiç değişmiyor; <b>{PLAYED_TO_LEVEL}. seviyede de 1. seviyedeki "
             "aynı market</b>. Seviye numarası dışında oyuncuya ne kadar ilerlediğini gösteren görsel bir işaret yok."),
            ("Rakip örneği",
             "Türün başarılı oyunlarında ilerleme ana ekranda görünüyor. Good Job Games'in <b>Match Villains</b> "
             "oyununda arka plan <b>her 20 seviyede bir</b> değişiyor. Dream Games'in <b>Royal Match</b> ve "
             "<b>Royal Kingdom</b> oyunlarında saray, oyuncu ilerledikçe sürekli büyüyor. <b>Manor Cafe</b>'de ise "
             "kafe hem büyüyor hem de oyuncu onu kendi zevkine göre <b>özelleştirebiliyor</b>."),
            ("Öneri",
             "Market seviyelerle birlikte büyüsün: mahalle bakkalından (<b>Corner Shop</b>) markete "
             "(<b>Fresh Market</b>), oradan lüks bir alışveriş merkezine (<b>Gourmet Plaza</b>). Her ~20 seviyede "
             "yeni bir aşama açılsın ve geçiş kısa bir açılış animasyonuyla kutlansın."),
            ("Daha ucuz alternatif",
             "Sıfırdan tasarıma gerek yok: <b>Order Journey</b>'deki aşama sahneleri (lunapark, sinema …) oyunda "
             "zaten hazır. Oyuncu bir aşamayı bitirdikçe o sahne <b>ana ekranın arka planına</b> konursa, yeni "
             "çizim yapmadan da ilerleme hissi verir. Eforu düşük olduğu için ilk adım olarak denenebilir; tam "
             "market büyümesi sonra gelir."),
        ],
        metrics=["Aşama değişen seviyelerden sonra D1/D7 dönüş oranı", "Oturum başına oynanan seviye sayısı",
                 "Bir sonraki aşamaya yaklaşan oyuncuların churn oranı"],
        effort="Orta", impact="Yüksek",
        sequence=True,
        images=[("market-stage-1.jpg", "KONSEPT", "1 · Bakkal", True),
                ("market-stage-2.jpg", "KONSEPT", "2 · Market", True),
                ("market-stage-3.jpg", "KONSEPT", "3 · Lüks market", True)],
        # Second strip for the cheaper alternative; shown once the mockups are in assets/recs.
        strips_alt=[("KONSEPT · ORDER JOURNEY SAHNELERİYLE",
                     [("journey-stage-1.jpg", "1 · Lunapark"), ("journey-stage-2.jpg", "2 · Sinema"),
                      ("journey-stage-3.jpg", "3 · Sonraki sahne")])],
    ),
    dict(
        title="Malzemeye göre eşleşme sesleri",
        rows=[
            ("Bulgu",
             "Market Match'te hangi ürüne dokunulursa dokunulsun <b>aynı ses</b> çalıyor. Oysa oyunun mağazadaki "
             "sloganı <b>“Satisfying Supermarket Puzzle”</b>; yani oyunun ana vaadi tatmin edici bir his vermek ve "
             "ses bu hissin en önemli parçalarından biri."),
            ("Öneri",
             "<b>Dokunma sesi değişmesin.</b> Ürünler malzemesine göre gruplansın ve gruba özel ses "
             "yalnızca <b>3 ürün eşleşip raftan kaybolduğu anda</b> çalsın; böylece ses çeşitliliği olur ama "
             "karmaşa olmaz. "
             "<i>Bu bir hipotez; önce A/B testiyle doğrulanmalı.</i>"),
            ("Ses örnekleri", sound_table([
                ("Plastik paket", "cips, kurabiye paketi", "hışırtı"),
                ("Kutu içecek", "kola, gazoz", "“pısss” açılma sesi"),
                ("Cam şişe", "sos, meyve suyu", "tıngırtı"),
                ("Çikolata & şekerleme", "çikolata, sürpriz yumurta", "ambalaj yırtılma sesi"),
                ("Karton kutu", "kahve, mısır gevreği", "tok bir “tak”"),
            ])),
        ],
        metrics=["A/B testinde oturum süresi", "Oturum başına oynanan seviye sayısı", "D1 retention"],
        effort="Düşük", impact="Orta",
    ),
    dict(
        title="Reklam akışını oyuncuyu kaçırmayacak şekilde yeniden ayarla",
        rows=[
            ("Bulgu",
             f"1–3★ veren <b>{n_crit}</b> oyuncunun <b>{n_ads}</b>'sı reklamdan bahsediyor; şikâyetlerin en sık "
             "nedeni bu. Şikâyetler üç türe ayrılıyor: <b>sıklık</b> (“her seviye sonunda reklam”, “kısa sürede "
             "reklam yağmuruna tutuluyorsun”), <b>ödeme sorunu</b> (reklamsız paketi aldığı hâlde reklam gören "
             f"{n_noads} oyuncu) ve <b>yanıltıcı tanıtım</b> (reklam videosunun oyunla uyuşmadığını söyleyenler). "
             "309. seviyedeki bir oyuncu ayrıca bölüm sonu reklamının takıldığını ve oyunu her seferinde yeniden "
             "açmak zorunda kaldığını yazıyor."),
            *([("Oyuncular ne diyor", quotes_html)] if quotes_html else []),
            ("Öneri",
             "İlk seviyelerde ve kısa oturumlarda geçiş reklamı gösterme, seviye ve oturum başına bir tavan koy. "
             "Reklamsız paketin her durumda (güncelleme, yeniden yükleme, cihaz değişimi) çalıştığını test et ve "
             "bölüm sonu reklamının takılma hatasını incele. Tanıtım videolarını gerçek oynanışla uyumlu hâle getir."),
        ],
        metrics=["Reklam kaynaklı 1–3★ yorum sayısı", "D1/D7 retention (reklam tavanlı ve tavansız varyant)",
                 "Oturum başına reklam geliri", "Reklamsız paket sahiplerinde reklam gösterimi (0 olmalı)"],
        effort="Orta", impact="Yüksek",
    ),
    dict(
        title="Ayarları dişli ikonuna taşı, sekmeyi ilerleme için kullan",
        rows=[
            ("Bulgu",
             "Alt menüdeki 5 sekmeden biri <b>Ayarlar</b>. İçinde sadece müzik, ses, titreşim ve ipucu anahtarları, "
             "bildirim ayarı, destek ve yasal linkler var. Sık açılmayan bir ekran, navigasyonun en değerli "
             "alanlarından birini kaplıyor."),
            ("Öneri",
             "Ayarlar üst bardaki bir <b>dişli ikonuna</b> taşınsın ve boşalan sekmeye iki seçenekten biri gelsin: "
             "<b>İlerleme haritası</b>, yani 2. önerideki market aşamalarını (bakkal → market → lüks market) ve "
             "bir sonraki aşamaya kalan seviyeyi gösteren bir sayfa; ya da <b>sepet özelleştirme</b>, yani maskot "
             "alışveriş arabasının görünümünü coin'le değiştirme imkânı (coin'e can ve ekstra şans dışında yeni bir "
             "harcama alanı açar). "
             "Hangisinin seçileceğine A/B testi karar versin."),
            ("Industry benchmark",
             "En çok kazanan 500 oyunun <b>%70</b>'inde kozmetik/kilit açma satışı var (Appfigures, "
             "<i>Mobile Games in 2025</i>, s. 30); Market Match'te gözlenmedi. Sepet özelleştirme bu boşluğu "
             "kapatır. Ayrıntı: Sektörle Kıyas sayfası."),
        ],
        metrics=["Yeni sekmenin açılma oranı", "D7 retention", "Coin harcama oranı (özelleştirme varyantında)",
                 "Ayarlara erişimle ilgili destek talebi (artmamalı)"],
        effort="Düşük", impact="Orta",
    ),
]

if not RECS:
    C.empty_state("Öneriler hazırlanıyor",
                  "Her öneri; rakip oyundaki örneği, Market Match!'e nasıl uyarlanacağını ve "
                  "nasıl ölçüleceğini birlikte gösterecek.")

for i, r in enumerate(RECS, start=1):
    imgs = r.get("images") or []
    with st.container(key=f"rec-{i}"):
        if r.get("sequence"):
            # Progression: text on top, then the stages left -> right with arrows between them.
            C.product_rec(i, r["title"], r["rows"], r["metrics"], r["effort"], r["impact"])
            strips = [("KONSEPT · İLERLEME", [(f, c) for f, _t, c, _k in imgs])] + r.get("strips_alt", [])
            for s_no, (tag, shots) in enumerate(strips):
                shots = [(f, c) for f, c in shots if (ASSETS / f).exists()]  # skip mockups not added yet
                if not shots:
                    continue
                with st.container(key=f"strip-{i}-{s_no}"):
                    C.shot_tag(tag, concept=True)
                    spec = [.5] + [x for k in range(len(shots)) for x in ([.22, 1] if k else [1])] + [.5]
                    cols = st.columns(spec, vertical_alignment="top")[1:-1]  # screens top-aligned
                    for k, (file, caption) in enumerate(shots):
                        if k:
                            with cols[2 * k - 1]:
                                C.step_arrow()
                        with cols[2 * k]:
                            st.image(str(ASSETS / file), caption=caption, width="stretch")
            continue
        # Single screenshot: text left, phone right in a narrow column (2.8:1) so it is about as
        # tall as the text and the card stays a clean rectangle.
        text_col, img_col = (st.columns([1.35, 1] if len(imgs) > 1 else [2.8, 1], gap="large",
                                        vertical_alignment="center") if imgs else (st.container(), None))
        with text_col:
            C.product_rec(i, r["title"], r["rows"], r["metrics"], r["effort"], r["impact"])
        if img_col is not None:
            with img_col:
                for col, (file, tag, caption, concept) in zip(st.columns(len(imgs)), imgs):
                    with col:
                        C.shot_tag(tag, concept)
                        st.image(str(ASSETS / file), caption=caption, width="stretch")
