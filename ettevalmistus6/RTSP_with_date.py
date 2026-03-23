import cv2
import os
import time
import json
import numpy as np
from datetime import datetime, timedelta
from typing import List
import torch
from PIL import Image
from strhub.data.module import SceneTextDataModule
from dynamsoft_barcode_reader_bundle import *
from helpers import RTSPStreamReader, is_green_screen, measure_global_change, print_date_grid, get_formatted_date


# --- KONFIGURATSIOON ---
STREAM_URL = "rtsp://172.17.37.81:8554/kalkun"
MOTION_THRESHOLD = 15.0
CAPTURE_DELAY = 2.5
DYNAMSOFT_LICENSE = "t0084YQEAAIUx4hU4EqEOu9FaT9GprNtmXmbGA7IcvmG7V7l1yrR4WjV1JWPPrLuJoJN4HXVvqroIag2MeSFUJlbpkh0vhl8/Nrk3lffN1GzB7BvBtkl5"
DEBUG_MODE = False  # Silumisrežiim piltide salvestamiseks. Kui True, salvestatakse pildid kettale.
capture_date = datetime(2026, 2, 14)

#----------TODO nr 1 ----------------------
# VALI ENDA LEMMIK TUVASTUSMUDEL, defineeri vajalikud asjad (mudel, kasutamise funktsioon, mida for loopis kutsuda)
OCR_model = None

def tuvastus_X(image_batch: List[np.ndarray]) -> List[str]:
    return None # labels is already a list of strings
# --- End PARSeq OCR Inits ---




# --- Triipkoodi tuvastaja initsialiseerimine ---
LicenseManager.init_license(DYNAMSOFT_LICENSE)
router = CaptureVisionRouter()
template_path = "medium_template.json"
err_code, err_msg = router.init_settings_from_file(template_path)
if err_code != EnumErrorCode.EC_OK:
    print(f"Failed to load JSON settings from file: {err_msg}")
    exit()

with open('barcode_data.json', 'r') as f:
    barcode_data = json.load(f)

folder_name = STREAM_URL.split('/')[-1]
os.makedirs(folder_name, exist_ok=True)
stream = RTSPStreamReader(STREAM_URL)
time.sleep(2)

# --- Statistika muutujad (kogu takti kohta) ---
all_takt_processing_times = [] # Kogu takti töötlemise aeg (liikumise tuvastamisest piltide salvestamiseni)
all_barcode_processing_times = [] # Ainult triipkoodi lugemise aeg
all_date_ocr_processing_times = [] # Ainult kuupäevatuvastuse aeg
success_count = 0
stats_counts = [] # Leitud triipkoodide arv takti kohta
total_triggers = 0
started = False
green_cooldown = False
motion_triggered = False
trigger_time = 0
cycle_start_time = 0
current_product = None # we maintain a "current product", if a given frame does not have barcode, we proceed with last ean
required_keys = ["rois", "date_area", "label1_below", "label2_above", "product_area_between"]
# ------------------------------------------------
print(f"Ühendatud vooga {STREAM_URL}. Ootan rohelist märguannet...")

try:
    while True:
        start_t = time.perf_counter()

        ret1, frame1 = stream.read()
        time.sleep(0.02) # Väike paus, et kaadrid jõuaksid muutuda
        ret2, frame2 = stream.read()
        if not ret1 or not ret2: break

        now = time.time()
        current_is_green = is_green_screen(frame2)
        
        if not started:
            if current_is_green:
                print(">>> Roheline ekraan tuvastatud! Alustame tsüklit.")
                started = True
                green_cooldown = True
        else:
            process_this_frame = False
            if not current_is_green and green_cooldown:
                print(">>> Roheline ekraan lõppes. Alustame monitooringut.")
                green_cooldown = False
                cycle_start_time = now
                total_triggers += 1
                process_this_frame = True # Alusta töötlemist kohe pärast rohelise ekraani lõppu
            elif not green_cooldown:
                if current_is_green:
                    print(">>> Järgmine roheline ekraan tuvastatud. Lõpetan tsükli.")
                    break

                # Mõõdame liikumist
                mae = measure_global_change(frame1, frame2)
                if mae > MOTION_THRESHOLD and not motion_triggered:
                    motion_triggered = True
                    trigger_time = now
                    total_triggers += 1
                    print("\n ------------- \n")
                    print(f"[{now - cycle_start_time:.2f}s] Liikumine tuvastatud! Ootan {CAPTURE_DELAY}s...")

                if motion_triggered and (now - trigger_time >= CAPTURE_DELAY): # Kui liikumine tuvastatud ja ooteaeg möödas
                    process_this_frame = True
                    motion_triggered = False

            if process_this_frame:
                # --- Takti töötlemise algus (pärast liikumise tuvastamist/rohelise ekraani lõppu) ---
                takt_start_time = time.perf_counter()

                now = time.time()
                elapsed = now - cycle_start_time

                # --- Triipkoodi lugemine ---
                barcode_read_start_time = time.perf_counter()
                result = router.capture(frame2, "ReadBarcodes_Default")
                items = result.get_items() if result is not None else None
                barcode_read_end_time = time.perf_counter()
                barcodes = [item.get_text() for item in items or [] if item.get_type() == EnumCapturedResultItemType.CRIT_BARCODE]
                stats_counts.append(len(barcodes))

                # Get info from barcode_data.json
                if len(barcodes)>0:
                    success_count += 1
                    ean = barcodes[0] #just take the first one
                    product = barcode_data.get(ean) 
                    if product is None: # Kui tooteinfot EAN-i kohta ei leitud
                        print(f"[{elapsed:.2f}s] EAN {ean}: tooteinfot ei leitud.")
                        continue
                    # Uuendame globaalset tooteinfot ja salvestame EAN-i printimiseks
                    current_product = product.copy()
                    current_product["_ean"] = ean                        
                else:
                    print(f"[{elapsed:.2f}s] Triipkoode ei leitud.")
                
                # Kui meil pole varasemast taktist toodet ja praegu ei leidnud, siis katkestame
                if current_product is None:
                    print("Meil pole current_product teada. Katkestame takti töötlemise.")
                    continue
                # Kontrollime, et kõik vajalikud koordinaadid on olemas
                if not all(k in current_product for k in required_keys):
                    print(f"VIGA: Tooteinfot EAN {current_product.get('_ean')} on puudulik!")
                    continue
                    
                product_name = current_product.get("ITEMNAME", "Tundmatu toode")
                expiry_duration = current_product.get("BESTBEFOREDAYS", 0)
                expiry_date = capture_date + timedelta(days=expiry_duration)
                ean_str = current_product.get("_ean", "Tundmatu")
                print(f"[{elapsed:.2f}s] Kontekst: EAN {ean_str} | {product_name} | Aegub {expiry_date.strftime('%d.%m.%Y')}")

                # --- Kaadri juppideks lõikamise loogika ---
                temp_slices = []
                for pkg_id, coords in current_product["rois"].items():
                    x1, y1 = coords[0] # Koordinaadid täiskaadril
                    x2, y2 = coords[1]
                    roi_crop = frame2[y1:y2, x1:x2]
                    # Roteerime 90 kraadi vastupäeva
                    rotated = cv2.rotate(roi_crop, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    temp_slices.append(rotated)                    

                max_h = max(s.shape[0] for s in temp_slices)
                max_w = max(s.shape[1] for s in temp_slices)
                final_slices = [cv2.resize(s, (max_w, max_h)) for s in temp_slices]
                
                # --- TODO nr 2: Kuupäevade tuvastamine ---
                date_crops = []
                # final_slices on genereeritud current_product["rois"] järgi. Eeldame, et järjekord vastab kuvamisfunktsioonis visuaalsele paigutusele:
                # Top-Left, Bottom-Left, Top-Right, Bottom-Right
                for i, s_img in enumerate(final_slices):
                    # Koordinaadid juba normaliseeritud ja roteeritud tootepildil
                    dx1, dy1 = current_product["date_area"][0]
                    dx2, dy2 = current_product["date_area"][1]
                    date_crop = s_img[dy1:dy2, dx1:dx2]
                    date_crops.append(date_crop)


                ocr_start_time = time.perf_counter()
                detected_dates_raw = None # TODO, asenda siia sisse oma lemmiklahendus
                ocr_end_time = time.perf_counter() # Kuupäevatuvastuse lõpp
                    
                # Prindi ruudustik. detected_dates_raw on nüüd järjekorras Top-Left, Bottom-Left, Top-Right, Bottom-Right.
                expected_expiry_date_str = expiry_date.strftime('%d.%m.%Y')
                print_date_grid(detected_dates_raw, expected_expiry_date_str)

                # --- Salvesta takti ajastused ---
                takt_end_time = time.perf_counter()
                all_takt_processing_times.append((takt_end_time - takt_start_time) * 1000)
                all_barcode_processing_times.append((barcode_read_end_time - barcode_read_start_time) * 1000)
                all_date_ocr_processing_times.append((ocr_end_time - ocr_start_time) * 1000)

                # --- Kui soovid debugida, prindi iga takti ajastused ---
                #print(f"Takt {total_triggers} töötlemise ajad:")
                #print(f"  Kogu takti töötlemine (liikumise tuvastamisest): {(takt_end_time - takt_start_time)*1000:.2f} ms")
                #print(f"  Triipkoodi lugemine: {(barcode_read_end_time - barcode_read_start_time)*1000:.2f} ms")
                #print(f"  Kuupäevatuvastus (4 pilti): {(ocr_end_time - ocr_start_time)*1000:.2f} ms")
                print(f"[{elapsed:.2f}s] Takt {total_triggers} Töötlemine lõpetatud.")
                
                if DEBUG_MODE:
                    images_to_save = []
                    for sub in ["date", "label1", "label2", "product_area","individual_products","full_frames"]:
                        os.makedirs(os.path.join(folder_name, sub), exist_ok=True)
                    images_to_save.append((os.path.join(folder_name,"full_frames", f"takt_{total_triggers}_full.png"), frame2))

                    for i, s_img in enumerate(final_slices):
                        s_idx = i + 1
                        images_to_save.append((os.path.join(folder_name,"individual_products", f"takt_{total_triggers}_slice_{s_idx}.png"), s_img))
                            
                        # All-in-one lõikamine ja salvestusnimekirja lisamine
                        dx1, dy1 = current_product["date_area"][0]
                        dx2, dy2 = current_product["date_area"][1]
                        images_to_save.append((os.path.join(folder_name, "date", f"takt_{total_triggers}_s{s_idx}_date.png"), s_img[dy1:dy2, dx1:dx2]))
                                
                        images_to_save.append((os.path.join(folder_name, "label1", f"takt_{total_triggers}_s{s_idx}_l1.png"), s_img[current_product["label1_below"]:, :]))
                        images_to_save.append((os.path.join(folder_name, "label2", f"takt_{total_triggers}_s{s_idx}_l2.png"), s_img[:current_product["label2_above"], :]))
                            
                        py1, py2 = current_product["product_area_between"]
                        images_to_save.append((os.path.join(folder_name, "product_area", f"takt_{total_triggers}_s{s_idx}_prod.png"), s_img[py1:py2, :]))
                
                    save_start_t = time.perf_counter()
                    for path, img in images_to_save:
                        if img is not None and img.size > 0:
                            cv2.imwrite(path, img)
                    print(f"Piltide salvestamine võttis {(time.perf_counter() - save_start_t)*1000:.2f} ms")
                # --- Takti töötlemise lõpp ---

except KeyboardInterrupt:
    print("Peatatud.")

finally:
    stream.stop()

    # --- KOKKUVÕTE ---
    success_rate = (success_count / total_triggers * 100) if total_triggers else 0.0
    
    avg_total_takt_time = (sum(all_takt_processing_times) / len(all_takt_processing_times)) if all_takt_processing_times else 0.0
    max_total_takt_time = max(all_takt_processing_times) if all_takt_processing_times else 0.0

    avg_barcode_time = (sum(all_barcode_processing_times) / len(all_barcode_processing_times)) if all_barcode_processing_times else 0.0
    max_barcode_time = max(all_barcode_processing_times) if all_barcode_processing_times else 0.0

    avg_date_ocr_time = (sum(all_date_ocr_processing_times) / len(all_date_ocr_processing_times)) if all_date_ocr_processing_times else 0.0
    max_date_ocr_time = max(all_date_ocr_processing_times) if all_date_ocr_processing_times else 0.0

    avg_barcodes = (sum(stats_counts) / len(stats_counts)) if stats_counts else 0.0

    print("\n--- KOKKUVÕTE ---")
    print(f"Takte kokku: {total_triggers}")
    print(f"Triipkoodi tuvastamise õnnestumise protsent: {success_rate:.2f}%") 
    print(f"Keskmine kogu takti töötlemise aeg (liikumise tuvastamisest): {avg_total_takt_time:.2f} ms")
    print(f"Maksimaalne kogu takti töötlemise aeg (liikumise tuvastamisest): {max_total_takt_time:.2f} ms")
    print(f"Keskmine triipkoodi lugemise aeg: {avg_barcode_time:.2f} ms")
    print(f"Maksimaalne triipkoodi lugemise aeg: {max_barcode_time:.2f} ms")
    print(f"Keskmine kuupäevatuvastuse aeg (4 pilti): {avg_date_ocr_time:.2f} ms")
    print(f"Maksimaalne kuupäevatuvastuse aeg (4 pilti): {max_date_ocr_time:.2f} ms")  
