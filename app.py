"""
Aplikasi Streamlit: AKSARA DAERAH DI INDONESIA
Fitur:
- Pilih aksara (Jawa / Bali) di sidebar + preview contoh
- Tab 1: Gambar huruf manual di canvas → simpan PNG + metadata
- Tab 2: Galeri hasil gambar random N
- Sidebar: Download semua hasil sebagai hasil.zip
"""

import os
import io
import csv
import time
import random
import zipfile
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas


# ============================================================
# KONFIGURASI & KONSTANTA
# ============================================================
st.set_page_config(
    page_title="AKSARA DAERAH DI INDONESIA",
    page_icon="🪶",
    layout="wide",
)

BASE_DIR = "data"
AKSARA_DIRS = {
    "jawa": os.path.join(BASE_DIR, "jawa"),
    "bali": os.path.join(BASE_DIR, "bali"),
}
CONTOH_DIR = os.path.join(BASE_DIR, "contoh")
METADATA_PATH = os.path.join(BASE_DIR, "metadata.csv")

# Daftar huruf dasar (silabis) untuk masing-masing aksara
HURUF_MAP = {
    "jawa": ["ha", "na", "ca", "ra", "ka", "da", "ta", "sa", "wa", "la",
             "pa", "dha", "ja", "ya", "nya", "ma", "ga", "ba", "tha", "nga"],
    "bali": ["ha", "na", "ca", "ra", "ka", "da", "ta", "sa", "wa", "la",
             "pa", "dha", "ja", "ya", "nya", "ma", "ga", "ba", "tha", "nga"],
}


# ============================================================
# FUNGSI UTILITAS
# ============================================================
def init_folders() -> None:
    """Membuat semua folder yang diperlukan jika belum ada."""
    for path in [*AKSARA_DIRS.values(), CONTOH_DIR]:
        os.makedirs(path, exist_ok=True)
    # Inisialisasi metadata.csv dengan header jika belum ada
    if not os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["aksara", "huruf", "filepath", "waktu"])


def save_image(image_rgba: np.ndarray, aksara: str, huruf: str) -> str | None:
    """
    Menyimpan gambar dari canvas ke folder aksara.
    Return: filepath jika sukses, None jika gagal.
    """
    if image_rgba is None:
        return None

    # Cek apakah canvas kosong (semua pixel putih transparan / kosong)
    rgb = image_rgba[:, :, :3]
    alpha = image_rgba[:, :, 3] if image_rgba.shape[2] == 4 else np.full(rgb.shape[:2], 255)
    if rgb.sum() == 0 and alpha.sum() == 0:
        return None
    # Deteksi canvas "kosong" (background putih, tanpa stroke)
    if np.all(rgb >= 250) and np.all(alpha == 0):
        return None

    # Konversi RGBA → PIL Image → RGB (background putih)
    img = Image.fromarray(image_rgba.astype("uint8"), "RGBA")
    background = Image.new("RGB", img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[3])  # pakai alpha sebagai mask

    # Simpan dengan timestamp unik
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"{huruf}_{timestamp}.png"
    filepath = os.path.join(AKSARA_DIRS[aksara], filename)
    background.save(filepath, "PNG")

    # Simpan metadata
    with open(METADATA_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([aksara, huruf, filepath, datetime.now().isoformat(timespec="seconds")])

    return filepath


def load_random_images(aksara: str, n: int) -> list[str]:
    """Mengambil N file gambar acak dari folder aksara."""
    folder = AKSARA_DIRS[aksara]
    if not os.path.isdir(folder):
        return []
    files = [f for f in os.listdir(folder) if f.lower().endswith(".png")]
    if not files:
        return []
    k = min(n, len(files))
    picks = random.sample(files, k)
    return [os.path.join(folder, f) for f in picks]


def create_zip() -> bytes:
    """Membuat file ZIP berisi folder jawa/ dan bali/."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for aksara, folder in AKSARA_DIRS.items():
            if not os.path.isdir(folder):
                continue
            for fname in os.listdir(folder):
                if fname.lower().endswith(".png"):
                    zf.write(os.path.join(folder, fname), arcname=f"{aksara}/{fname}")
        # Sertakan metadata jika ada
        if os.path.exists(METADATA_PATH):
            zf.write(METADATA_PATH, arcname="metadata.csv")
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# SIDEBAR
# ============================================================
def render_sidebar() -> str:
    """Render sidebar dan return aksara terpilih (lowercase)."""
    with st.sidebar:
        st.title("🪶 Menu")
        aksara_pilihan = st.selectbox(
            "Pilih Aksara",
            options=["Jawa", "Bali"],
            index=0,
            help="Pilih aksara daerah yang ingin dipelajari/digambar.",
        )
        aksara_key = aksara_pilihan.lower()

        st.markdown("### 📖 Contoh Aksara")
        contoh_path = os.path.join(CONTOH_DIR, f"{aksara_key}.png")
        if os.path.exists(contoh_path):
            st.image(
                contoh_path,
                caption=f"Contoh Aksara {aksara_pilihan}",
                use_container_width=True,
            )
        else:
            st.warning(
                f"⚠️ File contoh `{contoh_path}` belum tersedia.\n\n"
                f"Silakan taruh file **{aksara_key}.png** di folder `{CONTOH_DIR}/`."
            )

        st.markdown("---")
        st.markdown("### 📥 Unduh Hasil")

        jawa_count = len([f for f in os.listdir(AKSARA_DIRS["jawa"]) if f.endswith(".png")]) \
            if os.path.isdir(AKSARA_DIRS["jawa"]) else 0
        bali_count = len([f for f in os.listdir(AKSARA_DIRS["bali"]) if f.endswith(".png")]) \
            if os.path.isdir(AKSARA_DIRS["bali"]) else 0
        st.caption(f"Jawa: **{jawa_count}** gambar · Bali: **{bali_count}** gambar")

        if st.button("📥 Download Semua", use_container_width=True):
            zip_data = create_zip()
            st.session_state["zip_data"] = zip_data

        if "zip_data" in st.session_state:
            st.download_button(
                label="⬇️ Klik untuk unduh hasil.zip",
                data=st.session_state["zip_data"],
                file_name="hasil.zip",
                mime="application/zip",
                use_container_width=True,
            )

    return aksara_key


# ============================================================
# TAB 1: GAMBAR AKSARA
# ============================================================
def render_tab_gambar(aksara_key: str) -> None:
    st.header("✍️ Gambar Aksara")
    st.caption(
        f"Menggambar huruf **aksara {aksara_key.capitalize()}** menggunakan mouse. "
        "Setelah selesai, klik **💾 Simpan**."
    )

    col_pilih, col_stroke = st.columns([1, 1])
    with col_pilih:
        huruf = st.selectbox(
            "Pilih Huruf",
            options=HURUF_MAP[aksara_key],
            index=0,
            key=f"huruf_{aksara_key}",
        )
    with col_stroke:
        stroke_width = st.slider("Ketebalan Stroke", min_value=2, max_value=20, value=5, step=1)

    # Canvas
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=stroke_width,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=350,
        width=350,
        drawing_mode="freedraw",
        key=f"canvas_{aksara_key}_{huruf}_{st.session_state.get('canvas_reset', 0)}",
        update_streamlit=True,
    )

    st.markdown("---")
    col_save, col_reset = st.columns(2)

    with col_save:
        if st.button("💾 Simpan", type="primary", use_container_width=True):
            if canvas_result.image_data is None:
                st.error("❌ Canvas masih kosong. Silakan gambar terlebih dahulu.")
            else:
                filepath = save_image(canvas_result.image_data, aksara_key, huruf)
                if filepath:
                    st.success(f"✅ Berhasil disimpan: `{filepath}`")
                    st.image(filepath, caption=f"Hasil: {huruf}", width=200)
                else:
                    st.error("❌ Canvas masih kosong. Silakan gambar terlebih dahulu.")

    with col_reset:
        if st.button("🗑️ Reset Gambar", use_container_width=True):
            # Paksa re-mount canvas dengan key baru → canvas kosong
            st.session_state["canvas_reset"] = st.session_state.get("canvas_reset", 0) + 1
            st.rerun()


# ============================================================
# TAB 2: GALERI HASIL
# ============================================================
def render_tab_galeri(aksara_key: str) -> None:
    st.header("🖼️ Galeri Hasil")
    st.caption(
        f"Menampilkan gambar acak hasil gambar aksara **{aksara_key.capitalize()}**."
    )

    n = st.slider(
        "Jumlah gambar yang ditampilkan (N)",
        min_value=1, max_value=50, value=10, step=1,
    )

    images = load_random_images(aksara_key, n)
    if not images:
        st.info(
            f"📭 Belum ada gambar tersimpan untuk aksara **{aksara_key.capitalize()}**. "
            "Silakan gambar di Tab 1 terlebih dahulu."
        )
        return

    st.write(f"Menampilkan **{len(images)}** gambar acak:")
    cols = st.columns(4)
    for i, img_path in enumerate(images):
        fname = os.path.basename(img_path)
        huruf = fname.split("_")[0]
        with cols[i % 4]:
            st.image(img_path, use_container_width=True)
            st.caption(f"**{huruf}** · `{fname}`")


# ============================================================
# MAIN APP
# ============================================================
def main() -> None:
    init_folders()

    st.title("🪶 AKSARA DAERAH DI INDONESIA")
    st.markdown(
        "Aplikasi belajar & mendokumentasikan aksara daerah Indonesia — "
        "**Jawa** dan **Bali** — dengan menggambar langsung menggunakan mouse."
    )
    st.markdown("---")

    # Sidebar → aksara terpilih
    aksara_key = render_sidebar()

    # Body: 2 tab
    tab1, tab2 = st.tabs(["✍️ Gambar Aksara", "🖼️ Galeri Hasil"])
    with tab1:
        render_tab_gambar(aksara_key)
    with tab2:
        render_tab_galeri(aksara_key)


if __name__ == "__main__":
    main()