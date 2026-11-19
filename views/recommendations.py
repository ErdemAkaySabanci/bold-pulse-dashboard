"""Benim Ürün Önerilerim: the author's own product recommendations, written after playing the game.

Approach: not new ideas from scratch, but features proven in competing games and how each could be
integrated into Market Match!. Order on the page = order of RECS.
"""
from pathlib import Path

import streamlit as st

from src.ui import components as C

PLAYED_TO_LEVEL = 54
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
              "bana ait")

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
        source=(f"Kendi oyun deneyimim ({PLAYED_TO_LEVEL}. seviyeye kadar) · Manor Cafe: daha önce "
                "hazırladığım Gamegos case study'si"),
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
        ],
        metrics=["Aşama değişen seviyelerden sonra D1/D7 dönüş oranı", "Oturum başına oynanan seviye sayısı",
                 "Bir sonraki aşamaya yaklaşan oyuncuların churn oranı"],
        effort="Orta", impact="Yüksek",
        source=(f"Kendi oyun deneyimim ({PLAYED_TO_LEVEL}. seviyeye kadar) · Match Villains (Good Job Games) · "
                "Royal Match, Royal Kingdom (Dream Games) · Manor Cafe"),
        sequence=True,
        images=[("market-stage-1.jpg", "KONSEPT", "1 · Bakkal", True),
                ("market-stage-2.jpg", "KONSEPT", "2 · Market", True),
                ("market-stage-3.jpg", "KONSEPT", "3 · Lüks market", True)],
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
        source=f"Kendi oyun deneyimim ({PLAYED_TO_LEVEL}. seviyeye kadar) · App Store sayfasındaki slogan",
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
            C.product_rec(i, r["title"], r["rows"], r["metrics"], r["effort"], r["impact"], r["source"])
            with st.container(key=f"strip-{i}"):
                C.shot_tag("KONSEPT · İLERLEME", concept=True)
                spec = [.5] + [x for k in range(len(imgs)) for x in ([.22, 1] if k else [1])] + [.5]
                cols = st.columns(spec, vertical_alignment="top")[1:-1]  # screens top-aligned
                for k, (file, _tag, caption, _concept) in enumerate(imgs):
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
            C.product_rec(i, r["title"], r["rows"], r["metrics"], r["effort"], r["impact"], r["source"])
        if img_col is not None:
            with img_col:
                for col, (file, tag, caption, concept) in zip(st.columns(len(imgs)), imgs):
                    with col:
                        C.shot_tag(tag, concept)
                        st.image(str(ASSETS / file), caption=caption, width="stretch")
