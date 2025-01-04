import openai
import requests
from bs4 import BeautifulSoup
import pandas as pd
import traceback

import google.generativeai as genai
from langchain.schema.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from google.generativeai.types import HarmBlockThreshold
from google.ai.generativelanguage_v1 import HarmCategory

import os



# GPT 生成爬蟲代碼
def generate_crawler_code(url, target, additional_instruction="",error_code=""):
    prompt = f"""
    網址是：{url}
    請撰寫 Python 爬蟲代碼，使用 BeautifulSoup 提取 "{target}" 的內容。
    {additional_instruction}
    請直接提供完整的 Python 代碼，不需要多餘的描述。
    
    另外這是之前的code與錯誤的說明:
    {error_code}
    """
    '''
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "你是一位專業的爬蟲工程師。"},
            {"role": "user", "content": prompt}
        ]
    )
    '''
    response = ChatGoogleGenerativeAI(
                            #https://aistudio.google.com/app/u/1/apikey #api key查詢
                            google_api_key = 'AIzaSyCybXsfKIzqLT1tDG3Y3kwKqXpj7frPPVM',
                            model='gemini-1.5-flash',
                            temperature=1,
                            top_p=0.9,
                            seed=0,
                            safety_settings={
                                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT : HarmBlockThreshold.BLOCK_NONE,
                            
                        })
    ans=response.invoke(prompt)
    return ans.content


def execute_crawler_code(crawler_code, context={}):
    """
    執行 GPT 生成的爬蟲代碼，並捕捉執行錯誤回傳給 GPT 校正。
    """
    try:
        exec(crawler_code, context)
    except Exception as e:
        error_message = traceback.format_exc()
        print(f"執行代碼時發生錯誤：\n{error_message}")
        return error_message
    return context

def crawl_and_merge_data(date,error_thing=""):
    # 爬取「日盤」數據
    day_url = "https://www.taifex.com.tw/cht/3/futContractsDate"
    day_target = "日盤數據表格"
    day_crawler_code = generate_crawler_code(day_url, day_target, additional_instruction="加入日期參數，篩選出該日期資料。")
    day_cleaned_code = day_crawler_code.replace("```python", "").replace("```", "").strip()
    print("GPT 生成的日盤代碼：\n", day_cleaned_code)
    day_context = {}
    error = execute_crawler_code(day_cleaned_code, day_context)
    if error:
        print("需要調整日盤代碼！")
        crawl_and_merge_data(date,f"夜盤Code:\n{day_cleaned_code}\n夜盤錯誤輸出:\n{error}")
        return
    
    # 爬取「夜盤」數據
    night_url = "https://www.taifex.com.tw/cht/3/futContractsDateAh"
    night_target = "夜盤數據表格"
    night_crawler_code = generate_crawler_code(night_url, night_target, additional_instruction="加入日期參數，篩選出該日期資料。")
    night_cleaned_code = night_crawler_code.replace("```python", "").replace("```", "").strip()
    print("GPT 生成的夜盤代碼：\n", night_cleaned_code)
    night_context = {}
    error = execute_crawler_code(night_cleaned_code, night_context)
    if error:
        print("需要調整夜盤代碼！")
        crawl_and_merge_data(date,f"夜盤Code:\n{night_cleaned_code}\n夜盤錯誤輸出:\n{error}")
        return

    # 假設數據存儲在 `day_data` 和 `night_data`
    day_data = day_context.get("day_data", pd.DataFrame())
    night_data = night_context.get("night_data", pd.DataFrame())
    
    if day_data.empty or night_data.empty:
        crawl_and_merge_data(date,f"日盤Code:\n{day_cleaned_code}\n夜盤Code:\n{night_cleaned_code}\n錯誤輸出:\n數據抓取失敗，請檢查代碼！")
        return
    
    # 合併日盤與夜盤數據，計算未平倉口數
    night_data["未平倉口數"] = night_data["未平倉口數"].shift(1).fillna(0) + night_data["當日交易口數"]
    merged_data = pd.concat([day_data, night_data], ignore_index=True)
    
    # 輸出為 Excel 檔案
    output_file = f"taiwan_futures_{date}.xlsx"
    merged_data.to_excel(output_file, index=False)
    print(f"數據已保存至 {output_file}")

if __name__ == "__main__":
    # 指定目標日期
    target_date = "2024-10-3"
    crawl_and_merge_data(target_date)
