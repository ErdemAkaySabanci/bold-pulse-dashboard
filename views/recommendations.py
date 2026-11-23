"""Benim Ürün Önerilerim / My Product Recommendations: the author's own product recommendations,
written after playing the game.

Approach: not new ideas from scratch, but features proven in competing games and how each could be
integrated into Market Match!. Order on the page = order of RECS. Every text is T(turkish, english).
"""
from html import escape
from pathlib import Path

import streamlit as st

from src import insights
from src import metrics as M
from src.data import load
from src.i18n import T, is_en
from src.ui import components as C

PLAYED_TO_LEVEL = 84
ASSETS = Path(__file__).resolve().parents[1] / "assets" / "recs"
CONCEPT = T("KONSEPT", "CONCEPT")

C.hero(
    T("Benim Ürün Önerilerim", "My Product Recommendations"),
    T("Rakiplerden öğrenip Market Match!'e uyarlamak", "Learn from competitors, adapt it to Market Match!"),
    T("Market Match! belirli bir oyuncu kitlesine ulaştı ve yatırım aldı; büyümenin bir sonraki adımı, türde "
      "kendini kanıtlamış özellikleri oyuna doğru şekilde uyarlamak. "
      f"<b>{PLAYED_TO_LEVEL}. seviyeye</b> kadar oynadıktan sonra hazırladığım öneriler bu özelliklere ve "
      "Market Match!'e <b>nasıl entegre edilebileceklerine</b> odaklanıyor.",
      "Market Match! has reached a real audience and raised investment; the next step for growth is adapting "
      "features that have proven themselves in the genre. The recommendations below, written after playing to "
      f"<b>level {PLAYED_TO_LEVEL}</b>, focus on those features and <b>how they could be integrated</b> into "
      "Market Match!."),
)


def sound_table(rows: list[tuple[str, str, str]]) -> str:
    """Material -> example items -> sound, as a compact HTML table inside a card row."""
    body = "".join(f"<tr><td class='n'>{k}</td><td><b>{m}</b></td><td>{ex}</td><td><span class='snd'>{sd}</span></td></tr>"
                   for k, (m, ex, sd) in enumerate(rows, start=1))
    head = T("<th></th><th>Malzeme</th><th>Örnek ürünler</th><th>Eşleşmede çalan ses</th>",
             "<th></th><th>Material</th><th>Example items</th><th>Sound on match</th>")
    return f"<table class='p-rtable'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


C.data_source(T(f"Kendi oyun deneyimim ({PLAYED_TO_LEVEL}. seviyeye kadar) · rakip oyunlar · konsept görseller "
                "bana ait · reklam önerisinde mağaza yorumları",
                f"My own play-through (to level {PLAYED_TO_LEVEL}) · competing games · concept mockups are mine · "
                "store reviews for the ads recommendation"))

# --- Evidence for the ads card, computed from the same reviews as the Overview page (no hand-typed counts)
rv = load.reviews()
n_crit = int(rv["rating_bucket"].isin(["negative", "neutral"]).sum())
ad_rv = insights.ad_mentions(rv)
n_ads = len(ad_rv)
n_noads = int(rv["monetization"].map(lambda v: "no_ads_pack" in M.split_labels(v)).sum()) if "monetization" in rv else 0
# Two short player quotes (English originals) with a Turkish rendering in TR mode; skipped if missing.
QUOTES = [("after each level an ad will start and stop",
           "309 seviye oynadım, birden her seviyeden sonra reklam açılıp takılmaya başladı."),
          ("paid for the removal of ads",
           "Reklam mı görüyorum? Reklamları kaldırmak için para ödediğime eminim.")]
quotes_html = "".join(
    f"<div style='margin:.15rem 0'>“{escape(hit['text'].iloc[0][:150])}{'…' if len(hit['text'].iloc[0]) > 150 else ''}” "
    f"<span style='opacity:.75'>({hit['rating'].iloc[0]}★{'' if is_en() else ' · ' + escape(tr)})</span></div>"
    for key, tr in QUOTES
    if len(hit := ad_rv[ad_rv["text"].str.contains(key, case=False, regex=False)]))

FINDING, COMPETITOR, REC = T("Bulgu", "Finding"), T("Rakip örneği", "Competitor example"), T("Öneri", "Recommendation")

# One dict per recommendation. rows = (label, html) in reading order; images = (file, tag, caption, concept).
RECS: list[dict] = [
    dict(
        title=T("Boosterları zorunlu ve ücretsiz bir eğitimle öğret", "Teach boosters with a forced, free tutorial"),
        rows=[
            (FINDING,
             T("Üç booster (<b>Undo, Mixer, Scanner</b>) 2. seviyeden itibaren ekranda duruyor, mağazada paketlerle "
               "satılıyor (<b>Limited Deal 99,99 TL</b> · <b>Starter Bag 499,99 TL</b>) ve Order Journey'de "
               "kazanılıyor; ama <b>ilk 50 seviyede hiçbiri öğretilmiyor</b>. Oyuncudan, ne işe yaradığını "
               "bilmediği bir şey için para ödemesi bekleniyor.",
               "Three boosters (<b>Undo, Mixer, Scanner</b>) are on screen from level 2, sold in shop bundles "
               "(<b>Limited Deal 99.99 TRY</b> · <b>Starter Bag 499.99 TRY</b>) and won in Order Journey, yet "
               "<b>none of them is taught in the first 50 levels</b>. Players are asked to pay for something "
               "they don't understand.")),
            (COMPETITOR,
             T("Tam bir rakip olmasa da yine bir puzzle oyunu olan <b>Manor Cafe</b>, ilk boosterını "
               "<b>11.</b>, ikincisini <b>14. seviyede</b> ücretsiz haklarla tanıtıyordu.",
               "Not a direct competitor but also a puzzle game, <b>Manor Cafe</b> introduced its first booster at "
               "<b>level 11</b> and its second at <b>level 14</b>, with free charges.")),
            (REC,
             T("Her boosterı zorunlu bir eğitim ve 1 ücretsiz hakla tanıt: önce <b>Undo</b> (~10. seviye), "
               "diğer ikisi birkaç seviye arayla.",
               "Introduce each booster with a forced tutorial and one free charge: <b>Undo</b> first (around "
               "level 10), the other two a few levels apart.")),
        ],
        metrics=[T("İlk booster kullanımının seviyesi", "Level of first booster use"),
                 T("Booster paketlerinin satın alma oranı", "Purchase rate of booster bundles"),
                 T("Booster kullananlarla kullanmayanların retention farkı",
                   "Retention of booster users vs non-users")],
        images=[("booster-tutorial-concept.jpg", CONCEPT,
                 T("Zorunlu Undo eğitimi mockup'ı", "Forced Undo tutorial mockup"), True)],
    ),
    dict(
        title=T("Ana ekrandaki marketi oyuncuyla birlikte büyüt", "Grow the home-screen market with the player"),
        rows=[
            (FINDING,
             T(f"Ana ekranın arka planı oyun boyunca hiç değişmiyor; <b>{PLAYED_TO_LEVEL}. seviyede de 1. seviyedeki "
               "aynı market</b>. Seviye numarası dışında oyuncuya ne kadar ilerlediğini gösteren görsel bir işaret yok.",
               f"The home-screen background never changes: <b>at level {PLAYED_TO_LEVEL} it is the same market as at "
               "level 1</b>. Apart from the level number, nothing shows the player how far they have come.")),
            (COMPETITOR,
             T("Türün başarılı oyunlarında ilerleme ana ekranda görünüyor. Good Job Games'in <b>Match Villains</b> "
               "oyununda arka plan <b>her 20 seviyede bir</b> değişiyor. Dream Games'in <b>Royal Match</b> ve "
               "<b>Royal Kingdom</b> oyunlarında saray, oyuncu ilerledikçe sürekli büyüyor. <b>Manor Cafe</b>'de ise "
               "kafe hem büyüyor hem de oyuncu onu kendi zevkine göre <b>özelleştirebiliyor</b>.",
               "In the genre's successful games, progress shows on the home screen. In Good Job Games' <b>Match "
               "Villains</b> the background changes <b>every 20 levels</b>. In Dream Games' <b>Royal Match</b> and "
               "<b>Royal Kingdom</b> the castle keeps growing as the player advances. In <b>Manor Cafe</b> the cafe "
               "grows and the player can also <b>customize</b> it.")),
            (REC,
             T("Market seviyelerle birlikte büyüsün: mahalle bakkalından (<b>Corner Shop</b>) markete "
               "(<b>Fresh Market</b>), oradan lüks bir alışveriş merkezine (<b>Gourmet Plaza</b>). Her ~20 seviyede "
               "yeni bir aşama açılsın ve geçiş kısa bir açılış animasyonuyla kutlansın.",
               "Let the market grow with the levels: from a corner store (<b>Corner Shop</b>) to a supermarket "
               "(<b>Fresh Market</b>) and on to a luxury mall (<b>Gourmet Plaza</b>). Unlock a new stage about "
               "every 20 levels and celebrate the change with a short opening animation.")),
            (T("Daha ucuz alternatif", "Cheaper alternative"),
             T("Sıfırdan tasarıma gerek yok: <b>Order Journey</b>'deki aşama sahneleri (lunapark, sinema …) oyunda "
               "zaten hazır. Oyuncu bir aşamayı bitirdikçe o sahne <b>ana ekranın arka planına</b> konursa, yeni "
               "çizim yapmadan da ilerleme hissi verir. Eforu düşük olduğu için ilk adım olarak denenebilir; tam "
               "market büyümesi sonra gelir.",
               "No new design needed: the stage scenes in <b>Order Journey</b> (amusement park, cinema …) already "
               "exist in the game. Putting each finished stage's scene <b>behind the home screen</b> gives a sense "
               "of progress without new art. It is low effort, so it can be the first step; the full market "
               "growth can come later.")),
        ],
        metrics=[T("Aşama değişen seviyelerden sonra D1/D7 dönüş oranı", "D1/D7 return rate after stage-change levels"),
                 T("Oturum başına oynanan seviye sayısı", "Levels played per session"),
                 T("Bir sonraki aşamaya yaklaşan oyuncuların churn oranı",
                   "Churn of players close to the next stage")],
        sequence=True,
        images=[("market-stage-1.jpg", CONCEPT, T("1 · Bakkal", "1 · Corner shop"), True),
                ("market-stage-2.jpg", CONCEPT, T("2 · Market", "2 · Supermarket"), True),
                ("market-stage-3.jpg", CONCEPT, T("3 · Lüks market", "3 · Luxury market"), True)],
        # Second strip for the cheaper alternative; shown once the mockups are in assets/recs.
        strips_alt=[(T("KONSEPT · ORDER JOURNEY SAHNELERİYLE", "CONCEPT · WITH ORDER JOURNEY SCENES"),
                     [("journey-stage-1.jpg", T("Order Journey sahneleri (mevcut)", "Order Journey scenes (existing)")),
                      ("journey-stage-2.jpg", T("Seviye 30 · Lunapark", "Level 30 · Amusement park")),
                      ("journey-stage-3.jpg", T("Seviye 60 · Sinema", "Level 60 · Cinema"))])],
    ),
    dict(
        title=T("My Market: açılan kategorilerle dolan bir market",
                "My Market: a store that fills up with every category you unlock"),
        rows=[
            (FINDING,
             T("Bölüm geçtikçe yeni ürün kategorileri açılıyor ve her seviye sonunda bir kategori ilerlemesi "
               "gösteriliyor (ör. <b>“Personal Care 2/20”</b>). Ama oyuncu topladıklarını hiçbir yerde göremiyor: "
               "bu ilerleme bir sonraki seviyeye geçince ekrandan kayboluyor ve hiçbir şeye dönüşmüyor.",
               "New item categories unlock as levels are cleared, and every level ends with category progress "
               "(e.g. <b>“Personal Care 2/20”</b>). But players can't see what they have collected anywhere: the "
               "progress disappears when the next level starts and never turns into anything.")),
            (COMPETITOR,
             T("<b>Manor Cafe</b>'de oyuncu, ilerledikçe kafesini kaydırılabilir bir sahnede dolduruyor ve "
               "özelleştiriyor; ilerleme somut bir mekâna dönüşüyor.",
               "In <b>Manor Cafe</b> the player fills and customizes their cafe in a scrollable scene as they "
               "progress, so progress turns into a real place.")),
            (REC,
             T("Alt menüye bir <b>My Market</b> sekmesi eklensin: başta boş, Walmart tarzı reyonları olan, "
               "kaydırılabilir bir market. Her kategorinin (içecekler, soslar, kişisel bakım, dondurma …) kendi "
               "reyonu olsun; seviye sonundaki kategori çubuğu doldukça o reyonun rafları dolsun, yeni kategori "
               "açıldıkça yeni bir reyon açılsın. Böylece her seviye, oyuncunun kendi marketine eklenen somut bir "
               "parça olur. Sekmeye yer açmak için Ayarlar üst bardaki dişli ikonuna taşınabilir.",
               "Add a <b>My Market</b> tab to the bottom menu: a scrollable store with Walmart-style aisles that "
               "starts empty. Each category (drinks, sauces, personal care, ice cream …) gets its own aisle; as the "
               "end-of-level category bar fills, that aisle's shelves fill, and each newly unlocked category opens a "
               "new aisle. Every level becomes a visible piece of the player's own store. To make room for the tab, "
               "Settings can move to a gear icon in the top bar.")),
            (T("Sektör verisi", "Industry benchmark"),
             T("En çok kazanan 500 oyunun <b>%70</b>'inde kozmetik/kilit açma satışı var (Appfigures, "
               "<i>Mobile Games in 2025</i>, s. 30); Market Match'te gözlenmedi. My Market, ileride reyon ve vitrin "
               "süsleme gibi kozmetik satışlarına da zemin olur. Ayrıntı: Sektörle Kıyas sayfası.",
               "<b>70%</b> of the top 500 earning games sell cosmetics or unlocks (Appfigures, <i>Mobile Games in "
               "2025</i>, p. 30); none were seen in Market Match. My Market also lays the ground for cosmetic sales "
               "later, such as aisle and shop-window decorations. Details: Industry Benchmark page.")),
        ],
        metrics=[T("My Market sekmesinin açılma oranı", "Open rate of the My Market tab"),
                 T("Kategori tamamlama oranı", "Category completion rate"), "D7 / D30 retention",
                 T("Oturum başına oynanan seviye sayısı", "Levels played per session")],
        sequence=True,
        images=[],
        strips_alt=[(T("KONSEPT · MY MARKET", "CONCEPT · MY MARKET"),
                     [("my-market-tab.jpg", T("Ana ekranda yeni My Market sekmesi", "New My Market tab on Home")),
                      ("collection-progress.jpg", T("Seviye sonunda kategori ilerlemesi (oyunda var)",
                                                    "Category progress at level end (already in the game)")),
                      ("my-market-store.jpg", T("My Market: kategorilerle dolan market",
                                                "My Market: the store fills category by category"))])],
    ),
    dict(
        title=T("Malzemeye göre eşleşme sesleri", "Material-based match sounds"),
        rows=[
            (FINDING,
             T("Market Match'te hangi ürüne dokunulursa dokunulsun <b>aynı ses</b> çalıyor. Oysa oyunun mağazadaki "
               "sloganı <b>“Satisfying Supermarket Puzzle”</b>; yani oyunun ana vaadi tatmin edici bir his vermek ve "
               "ses bu hissin en önemli parçalarından biri.",
               "In Market Match the <b>same sound</b> plays whichever item you tap. Yet the game's store tagline is "
               "<b>“Satisfying Supermarket Puzzle”</b>: its core promise is a satisfying feel, and sound is one of "
               "the biggest parts of that feel.")),
            (REC,
             T("<b>Dokunma sesi değişmesin.</b> Ürünler malzemesine göre gruplansın ve gruba özel ses "
               "yalnızca <b>3 ürün eşleşip raftan kaybolduğu anda</b> çalsın; böylece ses çeşitliliği olur ama "
               "karmaşa olmaz. <i>Bu bir hipotez; önce A/B testiyle doğrulanmalı.</i>",
               "<b>Keep the tap sound as it is.</b> Group items by material and play the group's own sound only "
               "<b>when 3 items match and leave the shelf</b>: more variety in sound, without the noise. <i>This "
               "is a hypothesis and should be validated with an A/B test first.</i>")),
            (T("Ses örnekleri", "Sound examples"), sound_table([
                (T("Plastik paket", "Plastic pack"), T("cips, kurabiye paketi", "crisps, cookie packs"),
                 T("hışırtı", "rustle")),
                (T("Kutu içecek", "Canned drink"), T("kola, gazoz", "cola, soda"),
                 T("“pısss” açılma sesi", "“psst” can-opening sound")),
                (T("Cam şişe", "Glass bottle"), T("sos, meyve suyu", "sauce, juice"), T("tıngırtı", "clink")),
                (T("Çikolata & şekerleme", "Chocolate & candy"), T("çikolata, sürpriz yumurta", "chocolate, surprise egg"),
                 T("ambalaj yırtılma sesi", "wrapper tear")),
                (T("Karton kutu", "Cardboard box"), T("kahve, mısır gevreği", "coffee, cereal"),
                 T("tok bir “tak”", "a solid “thunk”")),
            ])),
        ],
        metrics=[T("A/B testinde oturum süresi", "Session length in the A/B test"),
                 T("Oturum başına oynanan seviye sayısı", "Levels played per session"), "D1 retention"],
    ),
    dict(
        title=T("Reklam akışını oyuncuyu kaçırmayacak şekilde yeniden ayarla",
                "Rework the ad flow so it stops driving players away"),
        rows=[
            (FINDING,
             T(f"1–3★ veren <b>{n_crit}</b> oyuncunun <b>{n_ads}</b>'sı reklamdan bahsediyor; şikâyetlerin en sık "
               "nedeni bu. Şikâyetler üç türe ayrılıyor: <b>sıklık</b> (“her seviye sonunda reklam”, “kısa sürede "
               "reklam yağmuruna tutuluyorsun”), <b>ödeme sorunu</b> (reklamsız paketi aldığı hâlde reklam gören "
               f"{n_noads} oyuncu) ve <b>yanıltıcı tanıtım</b> (reklam videosunun oyunla uyuşmadığını söyleyenler). "
               "309. seviyedeki bir oyuncu ayrıca bölüm sonu reklamının takıldığını ve oyunu her seferinde yeniden "
               "açmak zorunda kaldığını yazıyor.",
               f"<b>{n_ads}</b> of the <b>{n_crit}</b> players who gave 1–3★ mention ads, the most common reason for "
               "complaints. The complaints fall into three kinds: <b>frequency</b> (“an ad after every level”, "
               "“you get flooded with ads after a short while”), <b>payment</b> ("
               f"{n_noads} player still seeing ads after buying the no-ads pack) and <b>misleading promotion</b> "
               "(players saying the ad video doesn't match the game). A player at level 309 also writes that the "
               "end-of-level ad freezes and the game has to be restarted every time.")),
            *([(T("Oyuncular ne diyor", "What players say"), quotes_html)] if quotes_html else []),
            (REC,
             T("İlk seviyelerde ve kısa oturumlarda geçiş reklamı gösterme, seviye ve oturum başına bir tavan koy. "
               "Reklamsız paketin her durumda (güncelleme, yeniden yükleme, cihaz değişimi) çalıştığını test et ve "
               "bölüm sonu reklamının takılma hatasını incele. Tanıtım videolarını gerçek oynanışla uyumlu hâle getir.",
               "No interstitial ads in the first levels or in short sessions, and a cap per level and per session. "
               "Test that the no-ads pack works in every case (update, reinstall, new device) and investigate the "
               "end-of-level ad freeze. Make promo videos match the real gameplay.")),
        ],
        metrics=[T("Reklam kaynaklı 1–3★ yorum sayısı", "Number of ad-related 1–3★ reviews"),
                 T("D1/D7 retention (reklam tavanlı ve tavansız varyant)", "D1/D7 retention (capped vs uncapped variant)"),
                 T("Oturum başına reklam geliri", "Ad revenue per session"),
                 T("Reklamsız paket sahiplerinde reklam gösterimi (0 olmalı)",
                   "Ad impressions for no-ads pack owners (should be 0)")],
    ),
]

if not RECS:
    C.empty_state(T("Öneriler hazırlanıyor", "Recommendations in progress"),
                  T("Her öneri; rakip oyundaki örneği, Market Match!'e nasıl uyarlanacağını ve "
                    "nasıl ölçüleceğini birlikte gösterecek.",
                    "Each recommendation will show the competitor example, how to adapt it to Market Match! and "
                    "how to measure it."))

for i, r in enumerate(RECS, start=1):
    imgs = r.get("images") or []
    with st.container(key=f"rec-{i}"):
        if r.get("sequence"):
            # Progression: text on top, then the stages left -> right with arrows between them.
            C.product_rec(i, r["title"], r["rows"], r["metrics"])
            strips = ([(T("KONSEPT · İLERLEME", "CONCEPT · PROGRESSION"), [(f, c) for f, _t, c, _k in imgs])]
                      + r.get("strips_alt", []))
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
            C.product_rec(i, r["title"], r["rows"], r["metrics"])
        if img_col is not None:
            with img_col:
                for col, (file, tag, caption, concept) in zip(st.columns(len(imgs)), imgs):
                    with col:
                        C.shot_tag(tag, concept)
                        st.image(str(ASSETS / file), caption=caption, width="stretch")
