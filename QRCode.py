import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import zipfile
import arabic_reshaper
from bidi.algorithm import get_display

# إعداد الصفحة
st.set_page_config(
    page_title="QR Code Generator",
    layout="centered",
    page_icon="🔳"
)

# ✅ تصغير اختيار اللغة
lang_col, _ = st.columns([1, 5])
with lang_col:
    lang = st.selectbox("🌐", ["العربية", "English"], label_visibility="collapsed")

# الترجمة حسب اللغة
if lang == "العربية":
    title = "مولد QR Code"
    desc = "اختر الطريقة التي تريد بها توليد QR Code"
    manual_url = "📎 ادخل الرابط"
    manual_name = "🏷️ اسم الرابط"
    upload_label = "📁 (link & name) أو ارفع ملف اكسيل يحتوي على عمودين "
    generate_btn = "✅ توليد QR Code"
    zip_label = "📦 تحميل كل الأكواد كملف ZIP"
    single_label = "📥 تحميل QR Code"
    warn_empty = "⚠️ الرجاء إدخال رابط يدوي أو رفع ملف Excel."
    err_cols = "❌ الملف يجب أن يحتوي على الأعمدة: link و name"
    gen_success = "✅ تم توليد كل الأكواد بنجاح"
else:
    title = "QR Code Generator"
    desc = "Choose how you want to generate your QR Codes"
    manual_url = "📎 Enter URL:"
    manual_name = "🏷️ Enter QR Name:"
    upload_label = "📁 Or upload an Excel file with two columns (link & name)"
    generate_btn = "✅ Generate QR Code"
    zip_label = "📦 Download all codes as ZIP"
    single_label = "📥 Download QR Code"
    warn_empty = "⚠️ Please enter URL or upload an Excel file."
    err_cols = "❌ File must contain columns: link and name"
    gen_success = "✅ All QR codes generated successfully"

# ✅ عرض العنوان مع أيقونة QR
qr_icon_url = "https://api.iconify.design/mdi/qrcode.svg?color=DeepSkyBlue"
st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: -10px;">
        <img src="{qr_icon_url}" alt="QR Icon" width="40" height="40" style="margin-top: 5px;">
        <h1 style="color: #00BFFF; margin: 0;">{title}</h1>
    </div>
""", unsafe_allow_html=True)

# تحميل الخط
def get_font(size=32):
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except:
        return ImageFont.load_default()

# توليد صورة QR مع الاسم
def generate_qr_image(url, qr_name):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # 🔹 معالجة النص العربي إذا لزم
    try:
        reshaped_text = arabic_reshaper.reshape(qr_name)
        bidi_text = get_display(reshaped_text)
    except:
        bidi_text = qr_name

    font = get_font(32)
    bbox = font.getbbox(bidi_text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    padding = 40
    spacing = 20
    final_width = qr_img.size[0] + 2 * padding
    final_height = qr_img.size[1] + text_height + spacing + 2 * padding

    final_img = Image.new("RGB", (final_width, final_height), "black")
    final_img.paste(qr_img, (padding, padding))
    draw = ImageDraw.Draw(final_img)
    text_position = ((final_width - text_width) // 2, qr_img.size[1] + padding + spacing)
    draw.text(text_position, bidi_text, font=font, fill="white")

    return final_img

# الإدخال اليدوي
col1, col2 = st.columns(2)
with col1:
    url = st.text_input(manual_url)
with col2:
    qr_name = st.text_input(manual_name)

# رفع ملف Excel
uploaded_file = st.file_uploader(upload_label, type=["xlsx", "xls"])

# زر التوليد
if st.button(generate_btn):
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            df.columns = df.columns.str.lower()

            if not {'link', 'name'}.issubset(df.columns):
                st.error(err_cols)
            else:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
                    for idx, row in df.iterrows():
                        row_url = str(row['link']).strip()
                        row_name = str(row['name']).strip()
                        safe_name = row_name.replace("/", "_").replace("\\", "_").strip()
                        final_img = generate_qr_image(row_url, safe_name)
                        img_bytes = BytesIO()
                        final_img.save(img_bytes, format="PNG")
                        zip_file.writestr(f"{safe_name}_qr.png", img_bytes.getvalue())

                st.success(gen_success)
                st.download_button(
                    label=zip_label,
                    data=zip_buffer.getvalue(),
                    file_name="qr_codes.zip",
                    mime="application/zip"
                )

        except Exception as e:
            st.error(f"❌ {e}")

    elif url:
        final_img = generate_qr_image(url, qr_name)
        buf_display = BytesIO()
        final_img.save(buf_display, format="PNG")
        st.image(buf_display.getvalue(), caption=qr_name)

        buf_download = BytesIO()
        final_img.save(buf_download, format="PNG")
        st.download_button(
            label=single_label,
            data=buf_download.getvalue(),
            file_name=f"{qr_name}_qr.png",
            mime="image/png"
        )
    else:
        st.warning(warn_empty)


