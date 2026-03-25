# Reaalajas kuupäevatuvastus ja OCR-mudelite integreerimine

Eesmärk on integreerida valitud optilise märgituvastuse (OCR) mudel reaalajas RTSP videovoo töötlemise süsteemi. Süsteem tuvastab konveieril liikuvad tooted, lõikab neist välja kuupäeva alad ja proovib tuvastada "parim enne" kuupäevad. Lõpuks analüüsime lahenduse jõudlust ja arutame võimalikke parendusi.

## Tutvu failidega: `RTSP_with_date.py` ja `helpers.py`

Helpers.py failis on implementeeritud kõik OCR lahendused, mida kasutasime. Samuti uued kasutusviisid VLMi jaoks. Vaata neid põhjalikult, loe prompte.

`RTSP_with_date.py` failis defineeritakse millist tuvastamise varianti kasutatakse ning adaptiivselt luuakse vastav tuvastusmudeli objekt ja kutsustakse õiget funktsiooni välja. See fail haldab ka vastuste kuvamist ja statistika kogumist.

## Ülesanne: Lahenduse testimine ja analüüs

Testi `RTSP_with_date.py` lahendusi ja analüüsi tulemusi.

**Testimine:**
    *   Käivita skript iga nelja RTSP voo jaoks:
        *   `rtsp://172.17.37.81:8554/rulaad`
        *   `rtsp://172.17.37.81:8554/kalkun`
        *   `rtsp://172.17.37.81:8554/veis`
        *   `rtsp://172.17.37.81:8554/salami`
    *   Muuda `STREAM_URL` vastavalt iga testi jaoks.
    *   Lase skriptil töötada piisavalt kaua, et koguda statistikat (nt kuni rohelise ekraani teistkordse ilmumiseni).



## Arutelu

1.  **Mudeli valik ja optimeerimine:**
    *   Millise OCR-mudeli valiksid sina?

2.  **Häire strateegia ("Alert"):**
    *   Kuidas defineeriksid "alerti" ehk millal peaks süsteem andma häire, et toote kuupäev on vale?
    *   Arvesta oma strateegia väljatöötamisel järgmiste teguritega:
        *   **OCR-i täpsus:** Mida nägid oma testides erinevate mudelite täpsuse kohta? Kui usaldusväärne on üksik tuvastus?
        *   **Liini töötamise loogika:** Kas sama toodet on võimalik mitu korda kontrollida? Kas on aega mitme pildi analüüsiks?
        *   **Äriline eesmärk:** Kui kriitiline on vale kuupäev (nt toiduohutus vs. lihtsalt vale info)? Mis on valesti tuvastamise hind?
    *   Paku välja konkreetne strateegia

3.  **Töötluskiirus:**
    *   Kas sinu lahenduse töötluskiirus (vaata "Keskmine kogu takti töötlemise aeg") on piisav reaalajas kasutamiseks, eeldades 1 takt iga 7 sekundi järel?

