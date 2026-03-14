# Kodutöö: Süsteemi integratsioon ja analüüs

Sinu ülesanne on ühendada taktituvastus (Task 2) ja triipkoodi lugemine (Seminar 3) üheks terviklikuks süsteemiks.

## Ülesande sisu
1. Tee koopia failist `RTSP_liikumine.py`.
2. Süsteem peab toimima kahe rohelise ekraani vahelisel ajal, reageerima liikumisele, ootama 2.5 sekundit, võtma pildi ja sellel tuvastama triipkoodi ja selle kaudu toote info.
3. Terminalis peab iga takti kohta ilmuma:
    *   Toote EAN13 kood, toote nimi.
    *   Säilivusaeg (video salvestamise kuupäev (14.02.2026 + säilivuse kestus andmebaasist).

## Analüüs ja statistika
Programmi lõpus (uuesti rohelise ekraanini jõudes) peab süsteem väljastama statistilise ülevaate:
*   **Tuvastusmäär:** Mitmel korral õnnestus kood leida, kui liikumine oli toimunud? 
*   **Jõudlus:** Mis oli keskmine ja maksimaalne aeg, mis kulus pildilt triipkoodi leidmiseks? 
*   **Maht:** Kui mitu triipkoodi tuvastati keskmiselt ühe pildi pealt?



## Esitamine
1) Esita täidetud Pythoni fail.
2) Esita oma väljundstatistika ja vasta küsimused selle kohta:
- Kas kaadrite arv, millel tuvastati triipkood, läheb kokku märgenditega (kaadrite arvuga, millel on alumisi silte) ja sellega, mida sa ise näed failides?
- Kas tuvastus on piisavalt kiire reaalajas kasutuse jaoks?
- Mitu triipkoodi oli keskmiselt tegelikult pildidl? Miks ei leitud neist suuremat hulka üles? Kas triipkoodide tuvastamise määr (mitu protsenti üles leiti) on piisav, et lahendust kasutada? 
