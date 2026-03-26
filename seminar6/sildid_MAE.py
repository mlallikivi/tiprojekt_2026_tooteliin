import os
import random
import time
from pathlib import Path

import cv2
import numpy as np


os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt


# --- KONFIGURATSIOON ---
toode = "salami"  # "rulaad", "salami", "veis", "kalkun"
use_grayscale = False
downscale_factor = 0.25  # Nt 0.5 jätab alles 50% mõõtmetest, 0.2 jätab 20%.
augment = False
debug_augmentation = False

# Augmentatsiooni tugevused
brightness_delta = 0.15  # +/-15% heleduse muutus
saturation_delta = 0.20  # +/-20% küllastuse muutus HSV ruumis
shift_fraction = 0.05    # nihe kuni 5% pildi laiusest/kõrgusest


SCRIPT_DIR = Path(__file__).resolve().parent
NO_LABEL_DIR = SCRIPT_DIR / "no_label"
OUTPUT_DIR = SCRIPT_DIR / "mae_histograms"
DEBUG_AUGMENT_DIR = SCRIPT_DIR / "augmented_debug"
LABEL_TYPES = ("label1", "label2")
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


def load_image_paths(folder: Path) -> list[Path]:
    if not folder.is_dir():
        raise FileNotFoundError(f"Kausta ei leitud: {folder}")

    return sorted(
        path for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def apply_downscale(image: np.ndarray, factor: float | None) -> np.ndarray:
    if factor is None or factor == 1.0:
        return image

    if factor <= 0:
        raise ValueError("downscale_factor peab olema positiivne arv.")

    new_width = max(1, int(round(image.shape[1] * factor)))
    new_height = max(1, int(round(image.shape[0] * factor)))
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)


def adjust_brightness(image: np.ndarray, delta: float) -> np.ndarray:
    factor = 1.0 + random.choice([-delta, delta])
    adjusted = image.astype(np.float32) * factor
    return np.clip(adjusted, 0, 255).astype(np.uint8)


def adjust_saturation(image: np.ndarray, delta: float) -> np.ndarray:
    factor = 1.0 + random.choice([-delta, delta])
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] *= factor
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def shift_image_with_edge_repeat(image: np.ndarray, shift_frac: float) -> np.ndarray:
    height, width = image.shape[:2]
    max_dx = max(1, int(round(width * shift_frac)))
    max_dy = max(1, int(round(height * shift_frac)))
    dx = random.choice([-max_dx, 0, max_dx])
    dy = random.choice([-max_dy, 0, max_dy])

    if dx == 0 and dy == 0:
        dx = max_dx

    pad_left = max(dx, 0)
    pad_right = max(-dx, 0)
    pad_top = max(dy, 0)
    pad_bottom = max(-dy, 0)

    padded = cv2.copyMakeBorder(
        image,
        pad_top,
        pad_bottom,
        pad_left,
        pad_right,
        borderType=cv2.BORDER_REPLICATE,
    )

    start_x = pad_right
    start_y = pad_bottom
    return padded[start_y:start_y + height, start_x:start_x + width]


def maybe_augment_image(image: np.ndarray, apply_augment: bool) -> tuple[np.ndarray, list[str]]:
    if not apply_augment:
        return image, []

    operations = [
        ("brightness", lambda img: adjust_brightness(img, brightness_delta)),
        ("saturation", lambda img: adjust_saturation(img, saturation_delta)),
        ("shift", lambda img: shift_image_with_edge_repeat(img, shift_fraction)),
    ]
    selected_count = random.randint(1, len(operations))
    selected_operations = random.sample(operations, selected_count)

    augmented = image.copy()
    applied_names: list[str] = []
    for name, operation in selected_operations:
        augmented = operation(augmented)
        applied_names.append(name)

    return augmented, applied_names


def save_debug_augmentation(
    image: np.ndarray,
    output_dir: Path,
    original_name: str,
    applied_augmentations: list[str],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    ops_tag = "_".join(applied_augmentations) if applied_augmentations else "noops"
    output_path = output_dir / f"{Path(original_name).stem}__{ops_tag}.png"
    cv2.imwrite(str(output_path), image)


def preprocess_image(
    image_path: Path,
    grayscale: bool,
    downscale: float | None,
    apply_augment: bool = False,
    enable_debug: bool = False,
    debug_output_dir: Path | None = None,
) -> np.ndarray:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Pilti ei saanud lugeda: {image_path}")

    image, applied_augmentations = maybe_augment_image(image, apply_augment)

    if apply_augment and enable_debug and debug_output_dir is not None:
        save_debug_augmentation(
            image=image,
            output_dir=debug_output_dir,
            original_name=image_path.name,
            applied_augmentations=applied_augmentations,
        )

    if grayscale:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    image = apply_downscale(image, downscale)
    return image


def mean_pixel_difference(reference: np.ndarray, candidate: np.ndarray) -> float:
    if reference.shape != candidate.shape:
        raise ValueError(
            f"Piltide mõõtmed ei ühti: {reference.shape} vs {candidate.shape}. "
            "Pildid peavad enne võrdlemist olema sama mõõduga."
        )

    diff = cv2.absdiff(reference, candidate)
    return float(np.mean(diff))


def compare_against_reference(
    reference_path: Path,
    candidate_paths: list[Path],
    grayscale: bool,
    downscale: float | None,
    apply_augment: bool,
    enable_debug: bool,
    debug_output_dir: Path | None,
) -> tuple[list[tuple[str, float]], float]:
    reference_image = preprocess_image(
        reference_path,
        grayscale,
        downscale,
        apply_augment=False,
        enable_debug=False,
        debug_output_dir=None,
    )
    results: list[tuple[str, float]] = []
    total_elapsed = 0.0

    for candidate_path in candidate_paths:
        start = time.perf_counter()
        candidate_image = preprocess_image(
            candidate_path,
            grayscale,
            downscale,
            apply_augment=apply_augment,
            enable_debug=enable_debug and apply_augment,
            debug_output_dir=debug_output_dir,
        )
        candidate_image = match_reference_shape(candidate_image, reference_image.shape)
        distance = mean_pixel_difference(reference_image, candidate_image)
        elapsed = time.perf_counter() - start

        results.append((candidate_path.name, distance))
        total_elapsed += elapsed

    average_seconds = total_elapsed / len(candidate_paths) if candidate_paths else 0.0
    return results, average_seconds


def match_reference_shape(candidate: np.ndarray, reference_shape: tuple[int, ...]) -> np.ndarray:
    if candidate.shape == reference_shape:
        return candidate

    target_height, target_width = reference_shape[:2]
    return cv2.resize(candidate, (target_width, target_height), interpolation=cv2.INTER_AREA)


def summarize_distances(distances: list[tuple[str, float]]) -> dict[str, float] | None:
    if not distances:
        return None

    values = np.array([value for _, value in distances], dtype=np.float32)
    return {
        "min": float(np.min(values)),
        "mean": float(np.mean(values)),
        "max": float(np.max(values)),
    }


def print_summary(title: str, distances: list[tuple[str, float]]) -> None:
    summary = summarize_distances(distances)
    if summary is None:
        print(f"{title}: võrdluspilte ei leitud.")
        return

    print(
        f"{title}: min={summary['min']:.2f}, "
        f"keskmine={summary['mean']:.2f}, max={summary['max']:.2f}"
    )


def print_top_list(title: str, distances: list[tuple[str, float]], count: int, reverse: bool) -> None:
    print(title)
    if not distances:
        print("  Võrdluspilte ei leitud.")
        return

    for filename, value in sorted(distances, key=lambda item: item[1], reverse=reverse)[:count]:
        print(f"  {filename}: {value:.2f}")


def build_histogram_filename(
    product_name: str,
    label_type: str,
    grayscale: bool,
    downscale: float | None,
    apply_augment: bool,
) -> str:
    grayscale_tag = "gray" if grayscale else "color"
    downscale_tag = f"ds{downscale}".replace(".", "p") if downscale is not None else "original"
    augment_tag = "aug" if apply_augment else "noaug"
    return f"{product_name}_{label_type}_{grayscale_tag}_{downscale_tag}_{augment_tag}_hist.png"


def save_histogram(
    product_name: str,
    label_type: str,
    present_distances: list[tuple[str, float]],
    missing_distances: list[tuple[str, float]],
    grayscale: bool,
    downscale: float | None,
    apply_augment: bool,
) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / build_histogram_filename(
        product_name,
        label_type,
        grayscale,
        downscale,
        apply_augment,
    )

    plt.figure(figsize=(10, 6))

    if present_distances:
        plt.hist(
            [value for _, value in present_distances],
            bins=20,
            alpha=0.65,
            label="Sildiga pildid",
            color="seagreen",
        )

    if missing_distances:
        plt.hist(
            [value for _, value in missing_distances],
            bins=20,
            alpha=0.65,
            label="Sildita pildid",
            color="tomato",
        )

    plt.title(
        f"Mean pixel difference: {product_name}/{label_type}\n"
        f"grayscale={grayscale}, downscale_factor={downscale}, augment={apply_augment}"
    )
    plt.xlabel("Keskmine pikslierinevus")
    plt.ylabel("Piltide arv")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def analyze_label_type(
    product_name: str,
    label_type: str,
    grayscale: bool,
    downscale: float | None,
    apply_augment: bool,
    enable_debug: bool,
) -> None:
    labeled_folder = SCRIPT_DIR / product_name / label_type
    no_label_folder = NO_LABEL_DIR / label_type

    labeled_paths = load_image_paths(labeled_folder)
    no_label_paths = load_image_paths(no_label_folder)

    if len(labeled_paths) < 2:
        raise ValueError(
            f"Kaustas {labeled_folder} peab olema vähemalt 2 pilti, "
            "et esimene oleks näidis ja ülejäänud võrdluspildid."
        )

    reference_path = labeled_paths[0]
    same_label_paths = labeled_paths[1:]
    labeled_debug_dir = DEBUG_AUGMENT_DIR / product_name / label_type / "labeled"
    no_label_debug_dir = DEBUG_AUGMENT_DIR / product_name / label_type / "no_label"

    print(f"\nAnalüüs: {product_name}/{label_type}")
    print(f"Näidispilt: {reference_path.name}")
    print(f"Sildiga võrdluspilte: {len(same_label_paths)}")
    print(f"Sildita võrdluspilte: {len(no_label_paths)}")
    if apply_augment and enable_debug:
        print(f"Augmenteeritud debug-pildid salvestatakse: {DEBUG_AUGMENT_DIR}")

    same_label_distances, same_label_avg_seconds = compare_against_reference(
        reference_path,
        same_label_paths,
        grayscale,
        downscale,
        apply_augment,
        enable_debug,
        labeled_debug_dir,
    )
    no_label_distances, no_label_avg_seconds = compare_against_reference(
        reference_path,
        no_label_paths,
        grayscale,
        downscale,
        apply_augment,
        enable_debug,
        no_label_debug_dir,
    )

    print_summary("Sildiga pildid", same_label_distances)
    print_summary("Sildita pildid", no_label_distances)
    print(f"Keskmine aeg ühe sildiga pildi võrdlemiseks: {same_label_avg_seconds:.4f} s")
    print(f"Keskmine aeg ühe sildita pildi võrdlemiseks: {no_label_avg_seconds:.4f} s")

    print_top_list("5 kõige kaugemat sildiga pilti:", same_label_distances, count=5, reverse=True)
    print_top_list("5 kõige lähemat sildita pilti:", no_label_distances, count=5, reverse=False)

    histogram_path = save_histogram(
        product_name,
        label_type,
        same_label_distances,
        no_label_distances,
        grayscale,
        downscale,
        apply_augment,
    )
    print(f"Histogramm salvestatud: {histogram_path}")


def main() -> None:
    print("Siltide mean pixel difference analüüs")
    print(f"Toode: {toode}")
    print(f"use_grayscale={use_grayscale}")
    print(f"downscale_factor={downscale_factor}")
    print(f"augment={augment}")
    print(f"debug_augmentation={debug_augmentation}")

    for label_type in LABEL_TYPES:
        analyze_label_type(
            toode,
            label_type,
            use_grayscale,
            downscale_factor,
            augment,
            debug_augmentation,
        )


if __name__ == "__main__":
    main()
