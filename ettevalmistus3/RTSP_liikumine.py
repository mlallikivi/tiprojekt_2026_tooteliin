import cv2
import os
import time
import numpy as np
import matplotlib.pyplot as plt
import threading

class RTSPStreamReader:
    def __init__(self, url):
        self.cap = cv2.VideoCapture(url)
        self.ret = False
        self.frame = None
        self.running = True
        threading.Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self.running:
            self.ret, self.frame = self.cap.read()
            if not self.ret: self.running = False

    def read(self):
        return self.ret, self.frame

    def stop(self):
        self.running = False
        self.cap.release()

"""
TÖÖ ENNE SEMINARI 3: Liikumise tuvastamine ja viivitusega salvestamine.

Eesmärk: Tuvastada konveieril liikumine, oodata pildi stabiliseerumist ja salvestada kaader.
"""

# --- KONFIGURATSIOON ---
# STREAM_URL = "rtsp://172.17.37.81:8554/salami"
# STREAM_URL = "rtsp://172.17.37.81:8554/veis"
# STREAM_URL = "rtsp://172.17.37.81:8554/kalkun"
STREAM_URL = "rtsp://172.17.37.81:8554/rulaad"

MOTION_THRESHOLD = 15.0  # Lävend, millest suurem muutus loetakse liikumiseks
CAPTURE_DELAY = 3      # Sekundid, mida oodatakse peale liikumise algust enne pildi tegemist

# Kausta loomine (eelmise ülesande lahendus)
folder_name = STREAM_URL.split('/')[-1]
os.makedirs(folder_name, exist_ok=True)

def is_green_screen(frame):
    """ Tuvastab rohelise märguande (eelmise ülesande lahendus). """
    if frame is None: return False
    small = cv2.resize(frame, (64, 64))
    avg_color = np.mean(small, axis=(0, 1))
    return avg_color[1] > 200 and avg_color[0] < 50 and avg_color[2] < 50

# --- ÜLESANNE: Muutuse mõõtmine ---
def measure_change(f1, f2):
    """
    Arvutab kahe kaadri vahelise erinevuse.
    Sinu ülesanne: 
    1. Mõõda funktsiooni täitmise aega.
    2. Testi arvutuse kiirust: kas piltide muutmine halltoonidesse ja väiksemaks annab olulist võitu?
    3. Arvuta MAE (Mean Absolute Error), MSE või mõni muu ise välja mõeldud erinevuse või liikumise mõõdik
    4. Prindi välja kulunud aeg ja tagasta arvutatud skoor.
    """
    # TODO: Sinu kood siia
    return 0.0

stream = RTSPStreamReader(STREAM_URL)
time.sleep(2)
if not stream.ret:
    print(f"Viga ühendusega: {STREAM_URL}")
    exit()

print(f"Seadistatud: Lävend {MOTION_THRESHOLD}, viivitus {CAPTURE_DELAY}s")

# --- ÜLESANNE: Logi salvestamine
# loo siin tühjad listid, et talletada info "muutuse graafik üle aja" jaoks ---


started = False
green_cooldown = False
motion_triggered = False
trigger_time = 0
cycle_start_time = 0
frame_count = 0

try:
    while True:
        # Loeme kaks järjestikust kaadrit
        ret1, frame1 = stream.read()
        time.sleep(0.02) # Väike paus, et kaadrid jõuaksid muutuda
        ret2, frame2 = stream.read()
        
        if not ret1 or not ret2: break

        now = time.time()
        current_is_green = is_green_screen(frame2)

        if not started:
            if current_is_green:
                print(">>> Alustame tsüklit!")
                started = True
                green_cooldown = True
        else:
            if not current_is_green:
                green_cooldown = False

            if current_is_green and not green_cooldown:
                print(">>> Lõpetame tsükli.")
                break

            # --- ÜLESANNE: Liikumise tuvastamine ja ajastus ---
            # 1. Kutsu välja measure_change() ja salvesta tulemus ka listi. salvesta ka ajahetk.
            # 2. Kui muutus ületab MOTION_THRESHOLD ja 'motion_triggered' on False:
            #    - Märgi liikumine tuvastatuks, salvesta hetke aeg 'trigger_time' muutujasse.
            # 3. Kui 'motion_triggered' on True ja 'CAPTURE_DELAY' aeg on täis:
            #    - Salvesta pilt (cv2.imwrite).
            #    - Reseti 'motion_triggered', et oodata järgmist liikumist.
            
            # TODO: Sinu kood siia
            pass

finally:
    stream.stop()
    # ÜLESANNE: joonista graafik, kasuta näiteks plt.plot(), plt.axhline()(lävendi jaoks), 
    # pane ka nimi ja telgede nimed. salvesta graafik faili
        plt.figure(figsize=(10, 5))
        #TODO

