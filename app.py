import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
from datetime import datetime

# 1. 設定網頁外觀與標題
st.set_page_config(page_title="公司發票上傳系統", page_icon="🧾")
st.title("🧾 業務發票自動報帳系統")
st.write("請業務同仁將發票拍照上傳，系統將自動辨識並回傳給會計部。")

# 2. 系統設定 (實務上 API Key 會隱藏在後台，這裡為了測試先做成輸入框)
api_key = st.text_input("請輸入系統驗證碼 (API Key)", type="password")

# 3. 建立上傳區塊 (手機瀏覽器開啟時，會自動跳出「相機」或「相簿」選項)
uploaded_file = st.file_uploader("點此拍照或上傳發票圖片", type=["jpg", "jpeg", "png"])

if uploaded_file is not None and api_key:
    # 顯示預覽圖
    st.image(uploaded_file, caption="發票預覽", width=300)
    
    # 建立送出按鈕
    if st.button("🚀 確認上傳並送出給會計"):
        with st.spinner("AI 正在幫您看發票中，請稍候..."):
            try:
                # 設定 AI
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # 讀取圖片
                img = PIL.Image.open(uploaded_file)
                
                # 給 AI 的指令
                prompt = """
                你是一位專業的台灣會計助理。請分析這張發票或收據圖片，提取資訊。
                請嚴格輸出為 JSON 格式，不要有其他廢話：
                {"發票日期": "YYYY-MM-DD", "發票號碼": "字軌與號碼", "買方統編": "8碼數字", "總金額": "阿拉伯數字"}
                """
                
                # 呼叫 AI
                response = model.generate_content([prompt, img])
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)
                
                # 加上業務員上傳的時間
                data["系統登記時間"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 4. 顯示成功訊息與結果
                st.success("✅ 發票辨識成功！資料已傳送給會計部。")
                
                # 用表格方式呈現給業務確認
                st.table(data)
                
                st.info("💡 系統提示：在完整版系統中，上述資料會在此刻自動寫入會計部的 Google Sheets 雲端硬碟中。")
                
            except Exception as e:
                st.error("❌ 辨識發生錯誤，請確保圖片清晰，或稍後再試。")
