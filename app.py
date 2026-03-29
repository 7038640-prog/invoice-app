import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
from datetime import datetime
import requests  # 新增的套件：用來把資料發送給 Google 表單

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
        with st.spinner("AI 正在幫您看發票，並努力寫入會計系統中..."):
            try:
                # 選擇模型
                valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                target_model = next((name for name in valid_models if 'flash' in name.lower()), None)
                if not target_model:
                    target_model = next((name for name in valid_models if 'pro' in name.lower()), valid_models[0])
                
                model = genai.GenerativeModel(target_model)
                img = PIL.Image.open(uploaded_file)
                
                # 包含「購買品項」與「報帳類別」的升級版 AI 指令
                prompt = """
                你是一位專業的台灣會計助理。請分析這張發票或收據圖片，提取資訊。
                1. 請將所有購買的商品名稱抓出來，組合成一個字串，用逗號隔開。
                2. 請根據購買內容，自動幫我推斷這筆花費的「報帳類別」(例如：餐飲費、交通費、辦公用品、交際費、雜支等)。
                
                請嚴格輸出為 JSON 格式，不要有其他廢話：
                {"發票日期": "YYYY-MM-DD", "發票號碼": "字軌與號碼", "買方統編": "8碼數字(若無填無)", "購買品項": "品項1, 品項2...", "報帳類別": "推斷的類別", "總金額": "阿拉伯數字"}
                """
                
                # 請 AI 產生內容
                response = model.generate_content([prompt, img])
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)
                data["系統登記時間"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # --- 將資料傳送給 Google 表單的神奇魔法 ---
                webhook_url = "https://script.google.com/macros/s/AKfycbwyKHqIQpogFqep--lRRGdWMIhAtReloywDWmIFB5FQRhsw92Y0tQrIvFhcwStoFbt2vw/exec"
                
                # 透過 requests 將整理好的資料 (data) 送出
                res = requests.post(webhook_url, json=data)
                
                if res.status_code == 200:
                    st.success("✅ 報帳大成功！資料已自動寫入 Google 會計總表。")
                    st.balloons() # 加上慶祝氣球特效！
                else:
                    st.warning("⚠️ 辨識成功，但寫入表單時發生異常，請聯絡系統管理員。")
                
                # 在畫面上印出結果讓業務確認
                st.table(data)
                
            except Exception as e:
                st.error(f"❌ 發生錯誤。錯誤詳情: {e}")
