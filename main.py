import firebase_admin
import streamlit as st
from colorthief import ColorThief
from PIL import Image, ImageDraw
import random, os, time, uuid, tomllib, json, asyncio
from firebase_admin import credentials, db
from telegram import Bot

supported_types = ["png", "jpg"]
palettes_dir = "palettes/"
max_file_age = 600

os.makedirs(palettes_dir, exist_ok=True)

if not os.path.exists("secretinfo/info.json"):
    os.makedirs("secretinfo/", exist_ok=True)
    with open(".streamlit/secrets.toml", "rb") as file:
        config = tomllib.load(file)
    json_data = json.dumps(config, indent=4)
    with open("secretinfo/info.json", "w") as jsonfile:
       jsonfile.write(json_data)

with open("secretinfo/info.json", "r", encoding="utf-8") as jsonforauth:
    secretdata = json.load(jsonforauth)
database_url = secretdata["dataBase_url"]
token = secretdata["token"]
chatid = secretdata["chatid"]

if not firebase_admin._apps:
    cred = credentials.Certificate("secretinfo/info.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': database_url
    })


async def send_message():
    bot = Bot(token=token)
    await bot.send_message(chat_id=chatid, text=f"Username:{st.session_state.username}\nComment:{st.session_state.comment}")

def submit():
    asyncio.run(send_message())

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
if "counter_ref" not in st.session_state:
    st.session_state.counter_ref = db.reference("/counter")
if "counter" not in st.session_state:
    st.session_state.counter = int
if "enable_feedback" not in st.session_state:
    st.session_state.enable_feedback = False
if "username" not in st.session_state:
    st.session_state.username = str
if "comment" not in st.session_state:
    st.session_state.comment = str


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
    st.session_state.counter = st.session_state.counter_ref.get() or 0
    st.session_state.counter += 1
    st.session_state.counter_ref.set(st.session_state.counter)
    st.session_state.enable_feedback = True
    generate_palette_image()


def cleanup_old_files():
    now = time.time()
    for filename in os.listdir(palettes_dir):
        file_path = os.path.join(palettes_dir, filename)
        if os.path.isfile(file_path) and (now - os.path.getmtime(file_path)) > max_file_age:
            os.remove(file_path)


cleanup_old_files()

st.write(f"Number of generated images-[{st.session_state.counter_ref.get()}]")

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
        st.markdown('<div style="margin: 30px 0;">', unsafe_allow_html=True)
        st.download_button(label="Download Image", data=file, file_name=f"palette_{st.session_state.random_filename}.png", mime="image/png")
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.enable_feedback:
    st.write("Leave Feedback")
    st.session_state.username = st.text_input("Username", placeholder="Username")
    st.session_state.comment = st.text_input("Comment", placeholder="Comment")
    st.button("Submit", on_click=submit)