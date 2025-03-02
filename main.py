import streamlit as st
from colorthief import ColorThief
from PIL import Image, ImageDraw

supported_types = ["png", "jpg"]


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


def get_colors():
    if st.session_state.uploaded_image is not None:
        process_image = ColorThief(st.session_state.uploaded_image)
        st.session_state.dominant_color = process_image.get_color(quality=1)
        if st.session_state.palette_size >= 8:
            st.session_state.palette = process_image.get_palette(color_count=st.session_state.palette_size + 1)
        else:
            st.session_state.palette = process_image.get_palette(color_count=st.session_state.palette_size)


uploaded_file = st.file_uploader("Upload Image", type=supported_types)

if uploaded_file:
    st.session_state.uploaded_image = uploaded_file
    st.image(uploaded_file, caption="Uploaded Image")
    st.session_state.get_color_button_disabled = False


st.session_state.palette_size = st.slider("Number Of Colors In Plaette", min_value=4, max_value=18, value=6)
st.button("Analyze Palette", disabled=st.session_state.get_color_button_disabled, on_click=get_colors)


if st.session_state.dominant_color:
    st.write(f"**Dominant Color:** RGB {st.session_state.dominant_color}")
    st.markdown(f"""
        <div style="width:50px; height:50px; background-color: rgb{st.session_state.dominant_color}; border-radius:10px;">
        </div>
        """, unsafe_allow_html=True)

if st.session_state.palette:
    st.write("**Color Palette:**")
    cols = st.columns(len(st.session_state.palette))
    for i, color in enumerate(st.session_state.palette):
        cols[i].markdown(f"""
            <div style="width:50px; height:50px; background-color: rgb{color}; border-radius:10px;">
            </div>
            """, unsafe_allow_html=True)