import openai
import requests
from bs4 import BeautifulSoup
import pandas as pd
import traceback
import subprocess
import google.generativeai as genai
from langchain.schema.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from google.generativeai.types import HarmBlockThreshold
from google.ai.generativelanguage_v1 import HarmCategory

import os

# 設定 Google Gemini API 參數
google_api_key = 'AIzaSyCybXsfKIzqLT1tDG3Y3kwKqXpj7frPPVM'
model = 'gemini-1.5-flash'
temperature = 0.5
top_p = 1
seed = 0

# 設定安全性選項
safety_settings = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
}

# 定義函數來呼叫 Gemini API
def invoke_gemini(prompt):
    response = ChatGoogleGenerativeAI(
        google_api_key=google_api_key,
        model=model,
        temperature=temperature,
        top_p=top_p,
        seed=seed,
        safety_settings=safety_settings
    )
    return response.invoke(prompt)

# 定義函數來檢查程式碼執行結果
def execute_python_code(code):
    try:
        # 將生成的程式碼保存到檔案
        with open("generated_code.py", "w", encoding="utf-8") as f:
            f.write("# -*- coding: utf-8 -*-\n" + code)
        
        # 執行該程式碼並捕獲輸出
        result = subprocess.run(
            ["python", "generated_code.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            if "error" in result.stdout:
                print("發現內部錯誤訊息，判定執行失敗：")
                return False, result.stdout
            print("程式執行成功！輸出如下：")
            print(result.stdout)
            if input("請檢查正確或錯誤(輸入正確/錯誤)")=="錯誤":
                return False, "錯誤"
            return True, result.stdout
        else:
            print("程式執行失敗，錯誤如下：")
            print(result.stderr)
            return False, result.stderr
    except Exception as e:
        print("執行程式時發生例外：", str(e))
        return False, str(e)


# 主迴圈
code = """#!/usr/bin/env python
# coding: utf-8

import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

# 初始化變量
url = "https://www.taifex.com.tw/cht/3/futContractsDate"
url_night = "https://www.taifex.com.tw/cht/3/futContractsDateAh"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

# 獲取當前腳本的路徑
current_dir = os.path.dirname(os.path.abspath(__file__))

# 檔案名
file_name = "hw2_A1105505.xlsx"

# 建立完整的檔案路徑
file_path = os.path.join(current_dir, file_name)

file_exist=0  # 初始設定檔案不存在
day_OR_night=0  # 設上一筆存到日盤

# 檢查是否存在 hw2_A1105505.xlsx 檔案
if os.path.exists(file_path):
    df_existing = pd.read_excel(file_path)
    last_date_str = df_existing['DATE'].max()
    start_date = datetime.strptime(last_date_str, "%Y/%m/%d")
    file_exist=1
    if pd.isna(df_existing.iloc[-1, 1]):  # 檢查 DataFrame 是否為空或最後一行第一欄是否為空
        day_OR_night= 1
    print(f"檔案已存在，從最新日期 {last_date_str} 開始爬取")
else:
    start_date = datetime.today() - timedelta(days=3*365)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"檔案不存在，請檢查工作目錄：{os.getcwd()}，從三年前的今天開始爬取 {start_date.strftime('%Y/%m/%d')}")

# 爬取到今日的數據
end_date = datetime.today()
data_list = []

delta = timedelta(days=1)
while start_date <= end_date:
    date_str = start_date.strftime("%Y/%m/%d")
    print(f"正在爬取 {date_str} 的資料...")
    
    # 略過程式碼中間的部分，僅顯示摘要
    # ...

# 保存 Excel
df_combined.to_excel(file_path, index=False)
print(f"數據已成功保存到 {file_path}")
"""


prompt = f'''請幫我撰寫一個 Python 程式(不准說明，只能撰寫python程式)，用來爬取台灣期貨交易所日盤與夜盤的期貨交易數據，並保存到 Excel 文件。程式需求如下：

            爬取網址：

            日盤數據：https://www.taifex.com.tw/cht/3/futContractsDate
            夜盤數據：https://www.taifex.com.tw/cht/3/futContractsDateAh
            功能描述：

            模擬瀏覽器的請求，需添加 User-Agent 標頭。
            程式需檢查當前目錄是否已存在名為 IR_Final_Prob1.xlsx 的文件：
            如果存在，從文件中最新的日期繼續爬取。
            如果不存在，從四個月前的今天開始爬取數據。
            數據處理邏輯：

            爬取的數據需進行處理，將日盤和夜盤的相關數據進行整合相加（包含自營商、投信和外資的多空淨額數據）。
            Excel 文件應包含以下欄位：DATE, 自營商多, 自營商空, 自營商多空淨額, 投信多, 投信空, 投信多空淨額, 外資多, 外資空, 外資多空淨額。
            比對資料：

            在成功保存 IR_Final_Prob1.xlsx 後，從中提取 DATE 為 2024/9/4 的資料。
            同時，讀取 hw2_A1105505.xlsx，提取 DATE 為 2024/9/4 的資料。
            比對這兩個 Excel 中該日期的資料：
            如果數據一致，則輸出成功消息。
            如果數據不一致，程式應報錯並結束執行。
            錯誤處理：

            添加適當的錯誤處理，包括爬取失敗、文件讀寫錯誤等情況。
            程式中需包含適當的註解，幫助理解邏輯流程。
            使用的主要庫：

            requests：用於 HTTP 請求。
            BeautifulSoup：用於解析 HTML 網頁。
            pandas：用於處理表格數據和 Excel 文件操作。
            
            另外以下是成功的code，你可以直接按照這個改:
            {code}
            '''
success = False
msg=""
generated_code=""
while not success:
    print("正在透過 Gemini 生成程式碼...")
    oricode = invoke_gemini(f"{prompt}\n以下是之前的錯誤訊息:{msg}\n以下是之前產生的code\n{generated_code}")
    generated_code = oricode.content.replace("```python", "").replace("```", "").strip()
    print("生成的程式碼如下：\n", generated_code)
    
    # 嘗試執行生成的程式碼
    success,msg = execute_python_code(generated_code)
    if not success:
        print("程式執行失敗，重新生成程式碼...\n")
    else:
        print("成功執行程式！")
