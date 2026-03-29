import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
from datetime import datetime

# 1. 系統設定：直接從 Streamlit 保險箱拿鑰匙，業務員完全看不到
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("系統找不到 API 金鑰，請確認 Streamlit Secrets 設定是否正確。")
    st.stop()

# 2. 設定網頁外觀與標題
st.set_page_config(page_title="公司發票上傳系統", page_icon="🧾")
st.title("🧾 業務發票自動報帳系統")
st.write("請業務同仁將發票拍照上傳，系統將自動辨識並回傳給會計部。")

# 3. 建立上傳區塊 (乾淨俐落，沒有密碼輸入框了)
uploaded_file = st.file_uploader("點此拍照或上傳發票圖片", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 顯示預覽圖
    st.image(uploaded_file, caption="發票預覽", width=300)
    
    # 建立送出按鈕
    if st.button("🚀 確認上傳並送出給會計"):
        with st.spinner("AI 正在幫您看發票中，請稍候..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                img = PIL.Image.open(uploaded_file)
                
                prompt = """
                你是一位專業的台灣會計助理。請分析這張發票或收據圖片，提取資訊。
                請嚴格輸出為 JSON 格式，不要有其他廢話：
                {"發票日期": "YYYY-MM-DD", "發票號碼": "字軌與號碼", "買方統編": "8碼數字", "總金額": "阿拉伯數字"}
                """
                
                response = model.generate_content([prompt, img])
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)
                data["系統登記時間"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                st.success("✅ 發票辨識成功！資料已傳送給會計部。")
                st.table(data)
                st.info("💡 系統提示：在完整版系統中，上述資料會在此刻自動寫入會計部的 Google Sheets 雲端硬碟中。")
                
            except Exception as e:
                # 把真實錯誤印出來，如果再失敗我們才知道原因
                st.error(f"❌ 辨識發生錯誤。錯誤代碼: {e}")
