import streamlit as st
from colorthief import ColorThief
from PIL import Image, ImageDraw
import random, os, time, uuid

supported_types = ["png", "jpg"]
palettes_dir = "palettes/"
max_file_age = 600

os.makedirs(palettes_dir, exist_ok=True)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "get_color_button_disabled" not in st.session_state:
    st.session_state.get_color_button_disabled = True
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "dominant_color" not in st.session_state:
    st.session_state.dominant_color = None
if "palette" not in st.session_state:
    st.session_state.palette = []
if "palette_size" not in st.session_state:
    st.session_state.palette_size = None
if "random_filename" not in st.session_state:
    st.session_state.random_filename = None
if "download_button_disabled" not in st.session_state:
    st.session_state.download_button_disabled = True


def generate_palette_image():
    if st.session_state.random_filename:
        old_file = os.path.join(palettes_dir, f"{st.session_state.random_filename}.png")
        if os.path.exists(old_file):
            os.remove(old_file)

    while True:
        st.session_state.random_filename = f"{st.session_state.session_id}_{random.randint(100000, 999999)}"
        file_path = os.path.join(palettes_dir, f"{st.session_state.random_filename}.png")
        if not os.path.exists(file_path):
            break

    img = Image.new("RGB", (st.session_state.palette_size * 16, 16), "white")
    draw = ImageDraw.Draw(img)
    for a, color_s in enumerate(st.session_state.palette):
        x1, x2 = a * 16, (a + 1) * 16
        draw.rectangle([x1, 0, x2, 16], fill=color_s)

    img.save(file_path, format="PNG")
    st.session_state.download_button_disabled = False


def get_colors():
    if st.session_state.uploaded_image:
        process_image = ColorThief(st.session_state.uploaded_image)
        st.session_state.dominant_color = process_image.get_color(quality=1)
        palette_size = max(4, st.session_state.palette_size)
        st.session_state.palette = process_image.get_palette(color_count=palette_size)
    generate_palette_image()


def cleanup_old_files():
    now = time.time()
    for filename in os.listdir(palettes_dir):
        file_path = os.path.join(palettes_dir, filename)
        if os.path.isfile(file_path) and (now - os.path.getmtime(file_path)) > max_file_age:
            os.remove(file_path)


cleanup_old_files()

uploaded_file = st.file_uploader("Upload Image", type=supported_types)

if uploaded_file:
    st.session_state.uploaded_image = uploaded_file
    st.image(uploaded_file, caption="Uploaded Image")
    st.session_state.get_color_button_disabled = False

st.session_state.palette_size = st.slider("Number Of Colors In Palette", min_value=4, max_value=18, value=6)

st.button("Analyze Palette", disabled=st.session_state.get_color_button_disabled, on_click=get_colors)

if st.session_state.dominant_color:
    st.write(f"**Dominant Color:** RGB {st.session_state.dominant_color}")
    st.markdown(
        f"""
        <div style="width:50px; height:50px; background-color: rgb{st.session_state.dominant_color}; border-radius:10px;">
        </div>
        """,
        unsafe_allow_html=True,
    )

if st.session_state.palette:
    st.write("**Color Palette:**")
    cols = st.columns(len(st.session_state.palette))
    for i, color in enumerate(st.session_state.palette):
        cols[i].markdown(
            f"""
            <div style="width:50px; height:50px; background-color: rgb{color}; border-radius:10px;">
            </div>
            """,
            unsafe_allow_html=True,
        )

palette_path = os.path.join(palettes_dir, f"{st.session_state.random_filename}.png")
if os.path.exists(palette_path):
    with open(palette_path, "rb") as file:
        st.download_button(
            label="Download Image",
            data=file,
            file_name=f"palette_{st.session_state.random_filename}.png",
            mime="image/png",
        )