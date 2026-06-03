"""
Tek seferlik script: mevcut 20 context'in tutarsızlıklarını düzeltir,
14 yeni senaryo (28 context + 168 sentence) ekler, 37 yeni filler ekler.
Çalıştırmadan önce backup_stimuli_*.json yazar.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.datalayer.database import get_firestore_client
from src.datalayer.repository import (
    ContextRepository,
    SentenceRepository,
    FillerRepository,
)
from src.datalayer.model import Context, Sentence, Filler


# ---------- BACKUP ----------

async def backup(db) -> dict:
    cr = ContextRepository(db)
    sr = SentenceRepository(db)
    fr = FillerRepository(db)
    contexts = await cr.list_all_ordered()
    data = {"timestamp": datetime.utcnow().isoformat(), "contexts": [], "fillers": []}
    for c in contexts:
        sents = await sr.find_by_context(c.id)
        data["contexts"].append({
            "context": c.to_dict(),
            "sentences": [s.to_dict() for s in sents],
        })
    fillers = await fr.list_all_ordered()
    data["fillers"] = [f.to_dict() for f in fillers]
    out = Path(f"backup_stimuli_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"✓ Backup saved: {out.name}")
    return data


# ---------- FIXES TO EXISTING ----------

TITLE_FIXES = {
    1: "Öykü-Betül-kütüphane-S bias",
    2: "Öykü-Betül-kütüphane-O bias",
    3: "Ahmet-Mehmet-eve girmek-S bias",
    4: "Ahmet-Mehmet-eve girmek-O bias",
    5: "Enes-Onur-trene binmek-S bias",
    6: "Enes-Onur-trene binmek-O bias",
    7: "Ayşe-Fatma-araba kullanmak-S bias",
    8: "Ayşe-Fatma-araba kullanmak-O bias",
    9: "Murat-Berk-parkta yürüyüş-S bias",
    10: "Murat-Berk-parkta yürüyüş-O bias",
    11: "Selim-Cem-selam vermek-S bias",
    12: "Selim-Cem-selam vermek-O bias",
    13: "Zeynep-Elif-kafede oturmak-S bias",
    14: "Zeynep-Elif-kafede oturmak-O bias",
    15: "Uğur-Hakan-güneşlenmek-S bias",
    16: "Uğur-Hakan-güneşlenmek-O bias",
    17: "Beyza-Sude-evden çıkma-S bias",
    18: "Beyza-Sude-evden çıkma-O bias",  # bug fix
    19: "Pelin-Derya-bahçede dolaş-S bias",
    20: "Pelin-Derya-bahçede dolaş-O bias",
}

SENTENCE_FIXES = {
    (9, 5):  "O parkta yürüyüş yaparken, Murat Berk'i aradı.",
    (10, 5): "O parkta yürüyüş yaparken, Murat Berk'i aradı.",
    (11, 5): "O sınıfa girerken, Selim Cem'e selam verdi.",
    (12, 5): "O sınıfa girerken, Selim Cem'e selam verdi.",
    (17, 2): "Beyza Sude'ye seslendiğinde, o evden çıkmaya hazırlanıyordu.",
    (17, 3): "Beyza Sude'ye seslendiğinde, kendisi evden çıkmaya hazırlanıyordu.",
    (18, 2): "Beyza Sude'ye seslendiğinde, o evden çıkmaya hazırlanıyordu.",
    (18, 3): "Beyza Sude'ye seslendiğinde, kendisi evden çıkmaya hazırlanıyordu.",
    (19, 1): "Pelin Derya'yı aradığında, bahçede dolaşıyordu.",
    (19, 2): "Pelin Derya'yı aradığında, o bahçede dolaşıyordu.",
    (19, 3): "Pelin Derya'yı aradığında, kendisi bahçede dolaşıyordu.",
    (19, 4): "Bahçede dolaşırken, Pelin Derya'yı aradı.",
    (19, 5): "O bahçede dolaşırken, Pelin Derya'yı aradı.",
    (19, 6): "Kendisi bahçede dolaşırken, Pelin Derya'yı aradı.",
    (20, 1): "Pelin Derya'yı aradığında, bahçede dolaşıyordu.",
    (20, 2): "Pelin Derya'yı aradığında, o bahçede dolaşıyordu.",
    (20, 3): "Pelin Derya'yı aradığında, kendisi bahçede dolaşıyordu.",
    (20, 4): "Bahçede dolaşırken, Pelin Derya'yı aradı.",
    (20, 5): "O bahçede dolaşırken, Pelin Derya'yı aradı.",
    (20, 6): "Kendisi bahçede dolaşırken, Pelin Derya'yı aradı.",
}


# ---------- NEW SCENARIOS ----------

NEW_SCENARIOS = [
    {"order_subject": 21, "order_object": 22, "title_root": "Burak-Kerem-antrenman",
     "context_subject": "Burak ile Kerem spor salonunda buluşmuştu. O an antrenman yapan Burak'tı; Kerem ise soyunma odasındaydı.",
     "context_object":  "Burak ile Kerem spor salonunda buluşmuştu. O an antrenman yapan Kerem'di; Burak ise soyunma odasındaydı.",
     "a": "Burak", "b_marker": "Kerem'i",
     "matrix_present": "selamladığında", "matrix_past": "selamladı",
     "action_progressive": "spor salonunda antrenman yapıyordu",
     "action_participle": "Spor salonunda antrenman yaparken"},

    {"order_subject": 23, "order_object": 24, "title_root": "Tolga-Eren-rapor",
     "context_subject": "Tolga ile Eren aynı şirketteydi. O an bilgisayarda rapor hazırlayan Tolga'ydı; Eren ise toplantıdaydı.",
     "context_object":  "Tolga ile Eren aynı şirketteydi. O an bilgisayarda rapor hazırlayan Eren'di; Tolga ise toplantıdaydı.",
     "a": "Tolga", "b_marker": "Eren'i",
     "matrix_present": "aradığında", "matrix_past": "aradı",
     "action_progressive": "bilgisayarda rapor hazırlıyordu",
     "action_participle": "Bilgisayarda rapor hazırlarken"},

    {"order_subject": 25, "order_object": 26, "title_root": "Furkan-Doruk-gitar",
     "context_subject": "Furkan ile Doruk aynı evdeydi. O sırada balkonda gitar çalan Furkan'dı; Doruk ise odadaydı.",
     "context_object":  "Furkan ile Doruk aynı evdeydi. O sırada balkonda gitar çalan Doruk'tu; Furkan ise odadaydı.",
     "a": "Furkan", "b_marker": "Doruk'a",
     "matrix_present": "seslendiğinde", "matrix_past": "seslendi",
     "action_progressive": "balkonda gitar çalıyordu",
     "action_participle": "Balkonda gitar çalarken"},

    {"order_subject": 27, "order_object": 28, "title_root": "Kaan-Yiğit-havuz",
     "context_subject": "Kaan ile Yiğit bir yaz tatilindeydi. O an havuzda yüzen Kaan'dı; Yiğit ise kenarda havlusunu seriyordu.",
     "context_object":  "Kaan ile Yiğit bir yaz tatilindeydi. O an havuzda yüzen Yiğit'ti; Kaan ise kenarda havlusunu seriyordu.",
     "a": "Kaan", "b_marker": "Yiğit'e",
     "matrix_present": "el salladığında", "matrix_past": "el salladı",
     "action_progressive": "havuzda yüzüyordu",
     "action_participle": "Havuzda yüzerken"},

    {"order_subject": 29, "order_object": 30, "title_root": "Mert-Emir-mangal",
     "context_subject": "Mert ile Emir komşuydu. O an bahçede mangal yakan Mert'ti; Emir ise çardakta sofrayı kuruyordu.",
     "context_object":  "Mert ile Emir komşuydu. O an bahçede mangal yakan Emir'di; Mert ise çardakta sofrayı kuruyordu.",
     "a": "Mert", "b_marker": "Emir'i",
     "matrix_present": "gördüğünde", "matrix_past": "gördü",
     "action_progressive": "bahçede mangal yakıyordu",
     "action_participle": "Bahçede mangal yakarken"},

    {"order_subject": 31, "order_object": 32, "title_root": "Barış-Tuna-alışveriş",
     "context_subject": "Barış ile Tuna marketteydi. O sırada raflar arasında alışveriş yapan Barış'tı; Tuna ise kasada sıradaydı.",
     "context_object":  "Barış ile Tuna marketteydi. O sırada raflar arasında alışveriş yapan Tuna'ydı; Barış ise kasada sıradaydı.",
     "a": "Barış", "b_marker": "Tuna'yı",
     "matrix_present": "fark ettiğinde", "matrix_past": "fark etti",
     "action_progressive": "raflar arasında alışveriş yapıyordu",
     "action_participle": "Raflar arasında alışveriş yaparken"},

    {"order_subject": 33, "order_object": 34, "title_root": "Ozan-Sarp-dağa tırmanmak",
     "context_subject": "Ozan ile Sarp dağ yürüyüşüne çıkmıştı. O sırada dağa tırmanan Ozan'dı; Sarp ise dinlenme noktasındaydı.",
     "context_object":  "Ozan ile Sarp dağ yürüyüşüne çıkmıştı. O sırada dağa tırmanan Sarp'tı; Ozan ise dinlenme noktasındaydı.",
     "a": "Ozan", "b_marker": "Sarp'a",
     "matrix_present": "yetiştiğinde", "matrix_past": "yetişti",
     "action_progressive": "dağa tırmanıyordu",
     "action_participle": "Dağa tırmanırken"},

    {"order_subject": 35, "order_object": 36, "title_root": "Ece-Defne-kek",
     "context_subject": "Ece ile Defne hafta sonu evdeydi. O an mutfakta kek pişiren Ece'ydi; Defne ise salonda kitap okuyordu.",
     "context_object":  "Ece ile Defne hafta sonu evdeydi. O an mutfakta kek pişiren Defne'ydi; Ece ise salonda kitap okuyordu.",
     "a": "Ece", "b_marker": "Defne'ye",
     "matrix_present": "seslendiğinde", "matrix_past": "seslendi",
     "action_progressive": "mutfakta kek pişiriyordu",
     "action_participle": "Mutfakta kek pişirirken"},

    {"order_subject": 37, "order_object": 38, "title_root": "Melis-İrem-fotoğraf",
     "context_subject": "Melis ile İrem sahildeydi. O sırada fotoğraf çeken Melis'ti; İrem ise mendireğin sonunda oturuyordu.",
     "context_object":  "Melis ile İrem sahildeydi. O sırada fotoğraf çeken İrem'di; Melis ise mendireğin sonunda oturuyordu.",
     "a": "Melis", "b_marker": "İrem'i",
     "matrix_present": "gördüğünde", "matrix_past": "gördü",
     "action_progressive": "sahilde fotoğraf çekiyordu",
     "action_participle": "Sahilde fotoğraf çekerken"},

    {"order_subject": 39, "order_object": 40, "title_root": "Nehir-Lara-kitap",
     "context_subject": "Nehir ile Lara aynı evi paylaşıyordu. O an salonda kitap okuyan Nehir'di; Lara ise antreye yeni gelmişti.",
     "context_object":  "Nehir ile Lara aynı evi paylaşıyordu. O an salonda kitap okuyan Lara'ydı; Nehir ise antreye yeni gelmişti.",
     "a": "Nehir", "b_marker": "Lara'yı",
     "matrix_present": "duyduğunda", "matrix_past": "duydu",
     "action_progressive": "salonda kitap okuyordu",
     "action_participle": "Salonda kitap okurken"},

    {"order_subject": 41, "order_object": 42, "title_root": "Esra-Cansu-meyve",
     "context_subject": "Esra ile Cansu pazara çıkmıştı. O sırada manavda meyve seçen Esra'ydı; Cansu ise börekçinin önündeydi.",
     "context_object":  "Esra ile Cansu pazara çıkmıştı. O sırada manavda meyve seçen Cansu'ydu; Esra ise börekçinin önündeydi.",
     "a": "Esra", "b_marker": "Cansu'yu",
     "matrix_present": "selamladığında", "matrix_past": "selamladı",
     "action_progressive": "manavda meyve seçiyordu",
     "action_participle": "Manavda meyve seçerken"},

    {"order_subject": 43, "order_object": 44, "title_root": "Buse-Gizem-dergi",
     "context_subject": "Buse ile Gizem öğle arasında kafedeydi. O sırada dergi okuyan Buse'ydi; Gizem ise kasada sipariş veriyordu.",
     "context_object":  "Buse ile Gizem öğle arasında kafedeydi. O sırada dergi okuyan Gizem'di; Buse ise kasada sipariş veriyordu.",
     "a": "Buse", "b_marker": "Gizem'i",
     "matrix_present": "aradığında", "matrix_past": "aradı",
     "action_progressive": "kafede dergi okuyordu",
     "action_participle": "Kafede dergi okurken"},

    {"order_subject": 45, "order_object": 46, "title_root": "Tuğçe-Yağmur-tablo",
     "context_subject": "Tuğçe ile Yağmur ressam atölyesindeydi. O sırada atölyede tablo yapan Tuğçe'ydi; Yağmur ise pencere kenarında çay içiyordu.",
     "context_object":  "Tuğçe ile Yağmur ressam atölyesindeydi. O sırada atölyede tablo yapan Yağmur'du; Tuğçe ise pencere kenarında çay içiyordu.",
     "a": "Tuğçe", "b_marker": "Yağmur'a",
     "matrix_present": "seslendiğinde", "matrix_past": "seslendi",
     "action_progressive": "atölyede tablo yapıyordu",
     "action_participle": "Atölyede tablo yaparken"},

    {"order_subject": 47, "order_object": 48, "title_root": "Nilay-Bahar-yoga",
     "context_subject": "Nilay ile Bahar evin terasındaydı. O sırada yoga yapan Nilay'dı; Bahar ise çiçekleri suluyordu.",
     "context_object":  "Nilay ile Bahar evin terasındaydı. O sırada yoga yapan Bahar'dı; Nilay ise çiçekleri suluyordu.",
     "a": "Nilay", "b_marker": "Bahar'ı",
     "matrix_present": "selamladığında", "matrix_past": "selamladı",
     "action_progressive": "terasta yoga yapıyordu",
     "action_participle": "Terasta yoga yaparken"},
]


def build_sentences(s: dict):
    a, b = s["a"], s["b_marker"]
    mp, mpst = s["matrix_present"], s["matrix_past"]
    ap, apar = s["action_progressive"], s["action_participle"]
    apar_low = apar[0].lower() + apar[1:]
    return [
        (1, f"{a} {b} {mp}, {ap}."),
        (2, f"{a} {b} {mp}, o {ap}."),
        (3, f"{a} {b} {mp}, kendisi {ap}."),
        (4, f"{apar}, {a} {b} {mpst}."),
        (5, f"O {apar_low}, {a} {b} {mpst}."),
        (6, f"Kendisi {apar_low}, {a} {b} {mpst}."),
    ]


SUBJECT_CORRECT = {1: True, 2: False, 3: True, 4: True, 5: False, 6: True}
OBJECT_CORRECT  = {1: False, 2: True, 3: False, 4: False, 5: True, 6: False}


# ---------- FILLERS ----------

NEW_FILLERS = [
    # ----- 18 basit -----
    (12, "Ali bugün okula yürüyerek gitti.", "Ali okula otobüsle gitti.", False),
    (13, "Mehmet pazartesi günü tatildeydi.", "Mehmet pazartesi günü çalışıyordu.", False),
    (14, "Sınavdan en yüksek notu Aslı aldı.", "Aslı sınavdan en düşük notu aldı.", False),
    (15, "Çiçekleri masaya Emine koydu.", "Masaya çiçek koyan Emine'ydi.", True),
    (16, "Yeni komşumuzun adı Selin.", "Yeni komşumuz Selin.", True),
    (17, "Mektubu posta kutusuna Murat bıraktı.", "Mektubu posta kutusuna bırakan Murat'tı.", True),
    (18, "Babam akşam erken yattı.", "Babam akşam geç yattı.", False),
    (19, "Çocuklar parkta top oynadı.", "Parkta top oynayan çocuklardı.", True),
    (20, "Köpek mutfakta uyuyordu.", "Mutfakta uyuyan köpekti.", True),
    (21, "Toplantı saat dokuzda başladı.", "Toplantı saat dokuzda bitti.", False),
    (22, "Dün sabah yağmur yağdı.", "Dün sabah hava açıktı.", False),
    (23, "Defteri Murat'a ben verdim.", "Defteri Murat'tan ben aldım.", False),
    (24, "Misafirler salondaydı.", "Misafirler salonda oturuyordu.", True),
    (25, "Kerem'in iki abisi var.", "Kerem'in tek abisi var.", False),
    (26, "Çayı taze demlediler.", "Demlenen çay tazeydi.", True),
    (27, "Pikniği geçen Pazar yaptılar.", "Piknik geçen Pazar yapıldı.", True),
    (28, "Sofrada üç kişi vardı.", "Sofrada dört kişi vardı.", False),
    (29, "Filmin başrolünde Cem Yılmaz vardı.", "Cem Yılmaz filmde rol aldı.", True),
    # ----- 19 maskeli -----
    (30, "Komşular bahçede mangal yakıyordu; Hasan ise terasa çıkmıştı.",
         "Komşular Hasan'a seslendiğinde, o terastaydı.", True),
    (31, "Öğretmenler toplantıdaydı; Aylin ise koridorda bekliyordu.",
         "Öğretmenler Aylin'i aradığında, o koridordaydı.", True),
    (32, "Çocuklar bahçede futbol oynuyordu; Kemal ise garajda araba tamir ediyordu.",
         "Çocuklar Kemal'i çağırdığında, o garajdaydı.", True),
    (33, "Arkadaşlar pikniğe gitmişti; Ferhat ise işteydi.",
         "Arkadaşlar Ferhat'a mesaj attığında, o piknik alanındaydı.", False),
    (34, "Misafirler salonda sohbet ediyordu; Banu ise mutfakta tatlı yapıyordu.",
         "Misafirler Banu'yu çağırdığında, o yatak odasındaydı.", False),
    (35, "Yengeler salonda film izliyordu; Ceren ise odasındaydı.",
         "Yengeler Ceren'e seslendiğinde, o odasındaydı.", True),
    (36, "Aile akşam yemeği için sofrayı kurdu; Yusuf ise dışarıda bekliyordu.",
         "Aile Yusuf'u aradığında, o evdeydi.", False),
    (37, "Akrabalar bahçede çay içiyordu; Demir ise içerideydi.",
         "Akrabalar Demir'i çağırdığında, o içerideydi.", True),
    (38, "Sınıf arkadaşları parkta buluştu; Sinan ise kütüphanedeydi.",
         "Sınıf arkadaşları Sinan'a mesaj attığında, o parktaydı.", False),
    (39, "Komşular apartmanın önünde sohbet ediyordu; Hülya ise balkondaydı.",
         "Komşular Hülya'ya seslendiğinde, o balkondaydı.", True),
    (40, "Çocuklar yemek odasındaydı; Aysun ise mutfaktaydı.",
         "Çocuklar Aysun'u çağırdığında, o yemek odasındaydı.", False),
    (41, "Aile salonda film izliyordu; Tarık ise garajdaydı.",
         "Aile Tarık'a seslendiğinde, o garajdaydı.", True),
    (42, "Arkadaşlar tatildeydi; Soner ise evindeydi.",
         "Arkadaşlar Soner'i aradığında, o tatil köyündeydi.", False),
    (43, "Komşular bahçeyi suluyordu; Refik ise sokağa çıkmıştı.",
         "Komşular Refik'i çağırdığında, o sokaktaydı.", True),
    (44, "Konuklar masadaydı; İlknur ise mutfaktaydı.",
         "Konuklar İlknur'a seslendiğinde, o yatak odasındaydı.", False),
    (45, "Arkadaşları kafeye gitmişti; Volkan ise sinemadaydı.",
         "Arkadaşları Volkan'a mesaj attığında, o sinemadaydı.", True),
    (46, "Sınıf öğrencileri sahaya çıktı; Yağız ise revirdeydi.",
         "Sınıf öğrencileri Yağız'a seslendiğinde, o sahadaydı.", False),
    (47, "Ekip toplantı odasındaydı; Pınar ise lobide bekliyordu.",
         "Ekip Pınar'ı çağırdığında, o lobideydi.", True),
    (48, "Akşam çekilişi yapılacaktı; Murat ise erken eve dönmüştü.",
         "Düzenleyiciler Murat'a mesaj attığında, o evdeydi.", True),
]


# ---------- MAIN ----------

async def main():
    db = get_firestore_client()
    cr = ContextRepository(db)
    sr = SentenceRepository(db)
    fr = FillerRepository(db)

    print("\n[1/4] Backup...")
    await backup(db)

    print("\n[2/4] Fixing titles on existing 20 contexts...")
    contexts = await cr.list_all_ordered()
    for c in contexts:
        new_title = TITLE_FIXES.get(c.order_index)
        if new_title and new_title != c.title:
            c.title = new_title
            c.updated_at = datetime.utcnow()
            await cr.save(c)
            print(f"  ✓ idx {c.order_index}: '{new_title}'")

    print("\n[3a/4] Fixing existing sentences...")
    fixed = 0
    for c in contexts:
        if c.order_index not in {9, 10, 11, 12, 17, 18, 19, 20}:
            continue
        sents = await sr.find_by_context(c.id)
        for s in sents:
            key = (c.order_index, s.position)
            if key in SENTENCE_FIXES and SENTENCE_FIXES[key] != s.text:
                s.text = SENTENCE_FIXES[key]
                s.updated_at = datetime.utcnow()
                await sr.save(s)
                fixed += 1
    print(f"  ✓ {fixed} sentence(s) updated")

    print(f"\n[3b/4] Creating {len(NEW_SCENARIOS)} new scenarios (×2 = {2*len(NEW_SCENARIOS)} contexts, {12*len(NEW_SCENARIOS)} sentences)...")
    for scen in NEW_SCENARIOS:
        ctx_s = Context.create(
            title=f"{scen['title_root']}-S bias",
            text=scen['context_subject'],
            bias='subject',
            order_index=scen['order_subject'],
        )
        await cr.save(ctx_s)
        ctx_o = Context.create(
            title=f"{scen['title_root']}-O bias",
            text=scen['context_object'],
            bias='object',
            order_index=scen['order_object'],
        )
        await cr.save(ctx_o)
        sentences = build_sentences(scen)
        for pos, text in sentences:
            await sr.save(Sentence.create(
                context_id=ctx_s.id, position=pos, text=text,
                correct_answer=SUBJECT_CORRECT[pos],
            ))
            await sr.save(Sentence.create(
                context_id=ctx_o.id, position=pos, text=text,
                correct_answer=OBJECT_CORRECT[pos],
            ))
        print(f"  ✓ idx {scen['order_subject']}/{scen['order_object']}  '{scen['title_root']}'")

    print(f"\n[4/4] Creating {len(NEW_FILLERS)} new fillers...")
    for order, ctx_text, sent_text, correct in NEW_FILLERS:
        await fr.save(Filler.create(
            context_text=ctx_text,
            sentence_text=sent_text,
            correct_answer=correct,
            order_index=order,
        ))
    print(f"  ✓ {len(NEW_FILLERS)} filler(s) created")

    # Final summary
    contexts = await cr.list_all_ordered()
    subj = [c for c in contexts if c.bias == "subject"]
    obj = [c for c in contexts if c.bias == "object"]
    fillers = await fr.list_all_ordered()
    print("\n=== DONE ===")
    print(f"Total contexts: {len(contexts)} (subject: {len(subj)} / 24, object: {len(obj)} / 24)")
    print(f"Total fillers : {len(fillers)}")


if __name__ == "__main__":
    asyncio.run(main())
