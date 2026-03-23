# Kodutöö: Reaalajas kuupäevatuvastus ja OCR-mudelite integreerimine

Selle kodutöö eesmärk on integreerida valitud optilise märgituvastuse (OCR) mudel reaalajas RTSP videovoo töötlemise süsteemi. Süsteem tuvastab konveieril liikuvad tooted, lõikab neist välja kuupäeva alad ja proovib tuvastada "parim enne" kuupäevad. Lõpuks analüüsime lahenduse jõudlust ja arutame võimalikke parendusi.

## Ülesanne 1: `RTSP_with_date.py` täiendamine

Failis `/ettevalmistus6/RTSP_with_date copy.py` on kaks `TODO` ala, mis vajavad täitmist.

1.  **TODO nr 1: OCR-mudeli valik ja initsialiseerimine**
    *   Vali üks seminaris käsitletud OCR-mudelitest: EasyOCR, PARSeq (strhub), PaddleOCR (paddlex) või OpenRouteri VLM.
    *   Initsialiseeri valitud mudel vastavalt selle dokumentatsioonile ja seminarimaterjalidele (`yl1_OCR.py`, `yl2_OCR.py`).
    *   Veendu, et kõik vajalikud impordid on faili alguses olemas.
    *   Näiteks PARSeq mudeli jaoks on vajalikud `torch`, `PIL.Image`, `strhub.data.module.SceneTextDataModule` ja `strhub.models.utils.create_model`.

2.  **TODO nr 2: OCR-funktsiooni väljakutsumine**
    *   Asenda `detected_dates_raw = None` rea asemel väljakutse oma valitud OCR-mudeli tuvastusfunktsioonile.
    *   Funktsioon peab võtma sisendiks `date_crops` (list `numpy.ndarray` kujul piltidest) ja tagastama listi tuvastatud toortekstidest.
    *   Näiteks PARSeq mudeli puhul oleks see `detected_dates_raw = tuvastus_parseq_for_rtsp(date_crops)`.

**Näpunäide:** Kui valid OpenRouteri mudeli, pead tõenäoliselt importima `OpenRouterOCR` klassi `helpers.py` failist ja initsialiseerima selle enne `try` plokki. Seejärel saad selle meetodit `tuvastus_openrouter` kasutada.

## Ülesanne 2: Lahenduse testimine ja analüüs

Pärast `RTSP_with_date.py` täiendamist testi oma lahendust ja analüüsi tulemusi.

1.  **Testimine:**
    *   Käivita skript iga nelja RTSP voo jaoks:
        *   `rtsp://172.17.37.81:8554/rulaad`
        *   `rtsp://172.17.37.81:8554/kalkun`
        *   `rtsp://172.17.37.81:8554/veis`
        *   `rtsp://172.17.37.81:8554/salami`
    *   Muuda `STREAM_URL` vastavalt iga testi jaoks.
    *   Lase skriptil töötada piisavalt kaua, et koguda statistikat (nt kuni rohelise ekraani teistkordse ilmumiseni).

2.  **Statistika:**
    *   Kogu ja esita iga voo kohta programmi lõpus väljastatav kokkuvõttev statistika:
        *   Takte kokku
        *   Triipkoodi tuvastamise õnnestumise protsent
        *   Keskmine kogu takti töötlemise aeg (liikumise tuvastamisest)
        *   Maksimaalne kogu takti töötlemise aeg (liikumise tuvastamisest)
        *   Keskmine triipkoodi lugemise aeg
        *   Maksimaalne triipkoodi lugemise aeg
        *   Keskmine kuupäevatuvastuse aeg (4 pilti)
        *   Maksimaalne kuupäevatuvastuse aeg (4 pilti)
        *   Keskmine leitud triipkoodide arv takti kohta

## Arutelu

Vasta järgmistele küsimustele:

1.  **Mudeli valik ja optimeerimine:**
    *   Millise OCR-mudeli valisid `RTSP_with_date.py` jaoks ja miks? Põhjenda oma valikut, viidates seminaris tehtud `yl1_OCR.py` ja `yl2_OCR.py` testide tulemustele (täpsus, kiirus, kulud).
    *   Kas tegid mingeid optimeerimisi (nt pildi eeltöötlus, mudeli seaded, batching) oma valitud mudeli jaoks? Kirjelda neid.

2.  **Häire strateegia ("Alert"):**
    *   Kuidas defineeriksid "alerti" ehk millal peaks süsteem andma häire, et toote kuupäev on vale?
    *   Arvesta oma strateegia väljatöötamisel järgmiste teguritega:
        *   **OCR-i täpsus:** Mida nägid oma testides erinevate mudelite täpsuse kohta? Kui usaldusväärne on üksik tuvastus?
        *   **Liini töötamise loogika:** Kas sama toodet on võimalik mitu korda kontrollida? Kas on aega mitme pildi analüüsiks?
        *   **Äriline eesmärk:** Kui kriitiline on vale kuupäev (nt toiduohutus vs. lihtsalt vale info)? Mis on valesti tuvastamise hind?
    *   Paku välja konkreetne strateegia (nt "kui vähemalt 3/4 tuvastatud kuupäevadest erinevad oodatavast", "kui tuvastatud kuupäev on oodatavast vanem kui X päeva", "kui kuupäevatuvastus ebaõnnestub X korda järjest").

3.  **Töötluskiirus:**
    *   Kas sinu lahenduse töötluskiirus (vaata "Keskmine kogu takti töötlemise aeg") on piisav reaalajas kasutamiseks, eeldades 1 takt iga 7 sekundi järel?
    *   Mida saaksid teha, et töötlust veelgi kiirendada? Paku välja konkreetseid strateegiaid (nt GPU kasutamine, mudeli optimeerimine, riistvara uuendamine, paralleelne töötlus, efektiivsem pildi eeltöötlus).

## Esitamine

Esita oma lahendus Moodle'is vastavalt juhistele.