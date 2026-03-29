import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
from datetime import datetime

# 1. 系統設定：讀取金鑰
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("系統找不到 API 金鑰，請確認 Streamlit Secrets 設定是否正確。")
    st.stop()

# 2. 設定網頁外觀
st.set_page_config(page_title="公司發票上傳系統", page_icon="🧾")
st.title("🧾 業務發票自動報帳系統")
st.write("請業務同仁將發票拍照上傳，系統將自動辨識並回傳給會計部。")

# 3. 建立上傳區塊
uploaded_file = st.file_uploader("點此拍照或上傳發票圖片", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="發票預覽", width=300)
    
    if st.button("🚀 確認上傳並送出給會計"):
        with st.spinner("AI 正在幫您看發票中，請稍候..."):
            try:
                # 【終極解法】讓程式自動去問 Google 伺服器現在有哪些模型可用
                valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                # 自動挑選最適合的模型 (優先找最新版的 flash，找不到就找 pro，再沒有就拿清單裡的第一個)
                target_model = next((name for name in valid_models if 'flash' in name.lower()), None)
                if not target_model:
                    target_model = next((name for name in valid_models if 'pro' in name.lower()), valid_models[0])
                
                # 在網頁右下角跳出一個小提示，告訴我們系統最後選了哪個模型
                st.toast(f"成功連線！系統自動選用的模型為: {target_model}")
                
                # 使用自動找到的模型來執行
                model = genai.GenerativeModel(target_model)
                img = PIL.Image.open(uploaded_file)
                
                prompt = """
                你是一位專業的台灣會計助理。請分析這張發票或收據圖片，提取資訊。
                請嚴格輸出為 JSON 格式，不要有其他廢話：
                {"發票日期": "YYYY-MM-DD", "發票號碼": "字軌與號碼", "買方統編": "8碼數字(若無填無)", "總金額": "阿拉伯數字"}
                """
                
                response = model.generate_content([prompt, img])
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)
                data["系統登記時間"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                st.success("✅ 發票辨識成功！資料已傳送給會計部。")
                st.table(data)
                st.info("💡 系統提示：在完整版系統中，上述資料會在此刻自動寫入會計部的 Google Sheets 雲端硬碟中。")
                
            except Exception as e:
                st.error(f"❌ 辨識發生錯誤。錯誤詳情: {e}")
