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
import time


def generate_crawler_code(url, target, additional_instruction="", error_code=""):
    """
    使用 GPT 生成爬蟲代碼
    """
    prompt = f"""
    網址是：{url}
    請撰寫 Python 爬蟲代碼，使用 BeautifulSoup 提取 "{target}" 的內容。
    {additional_instruction}
    以下是上次的代碼與錯誤說明： 
    {error_code}
    請改進代碼並直接提供完整的 Python 代碼，不需要多餘的描述。
    """
    response = ChatGoogleGenerativeAI(
        google_api_key='AIzaSyCybXsfKIzqLT1tDG3Y3kwKqXpj7frPPVM',
        model='gemini-1.5-flash',
        temperature=0.7,
        top_p=0.9,
        seed=0,
        safety_settings={ 
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        }
    )
    time.sleep(1)
    ans = response.invoke(prompt)
    return ans.content


def execute_crawler_code(crawler_code, context={}):
    """
    執行 GPT 生成的爬蟲代碼，並捕捉執行錯誤回傳給 GPT 校正。
    如果執行成功，返回 True 和上下文；否則返回 False 和錯誤訊息。
    """
    try:
        exec(crawler_code, context)
        return True, context  # 執行成功，返回 True 和上下文
    except Exception as e:
        error_message = traceback.format_exc()
        return False, error_message  # 執行失敗，返回 False 和錯誤訊息


def crawl_and_merge_data(date, feedback=""):
    # 爬取「日盤」數據
    day_url = "https://www.taifex.com.tw/cht/3/futContractsDate"
    day_target = "日盤數據表格"
    day_crawler_code = generate_crawler_code(day_url, day_target, additional_instruction="加入日期參數，篩選出該日期資料。", error_code=feedback)
    day_cleaned_code = day_crawler_code.replace("```python", "").replace("```", "").strip()

    print("GPT 生成的日盤代碼：\n", day_cleaned_code)

    day_context = {}
    success, result = execute_crawler_code(day_cleaned_code, day_context)
    print("執行結果：", result)
    
    # 檢查結果是否成功
    if not success:
        print("進入錯誤的success state:")
        print(f"錯誤訊息：\n{result}")
        user_feedback = input("請提供改進代碼的反饋：\n")
        crawl_and_merge_data(date, feedback=f"日盤Code:\n{day_cleaned_code}\n日盤錯誤輸出:\n{result}\n反饋：{user_feedback}")
        return
    else:
        # 顯示結果並詢問使用者是否符合預期
        day_data = day_context.get("day_data", pd.DataFrame())
        print("日盤數據：\n", day_data)
        
        user_feedback = input("日盤數據是否符合預期？(Yes/No/其他輸入):\n")
        
        if user_feedback.lower() == "yes":
            # 如果使用者輸入 Yes，則繼續執行後續步驟
            print("數據符合預期，繼續執行...")
        elif user_feedback.lower() == "no":
            # 如果使用者輸入 No，則重新生成代碼
            print("數據不符合預期，正在生成新的爬蟲代碼...")
            crawl_and_merge_data(date, feedback=f"日盤Code:\n{day_cleaned_code}\n日盤錯誤輸出:\n{result}\n反饋：數據不符合預期")
            return
        else:
            # 如果使用者輸入其他內容，請提供具體反饋並將反饋傳送給 GPT
            crawl_and_merge_data(date, feedback=f"日盤Code:\n{day_cleaned_code}\n日盤錯誤輸出:\n{result}\n反饋：{user_feedback}")
            return
    
    time.sleep(5)
#-----------------------------------------------------------
    # 爬取「夜盤」數據
    night_url = "https://www.taifex.com.tw/cht/3/futContractsDateAh"
    night_target = "夜盤數據表格"
    night_crawler_code = generate_crawler_code(night_url, night_target, additional_instruction="加入日期參數，篩選出該日期資料。", error_code=feedback)
    night_cleaned_code = night_crawler_code.replace("```python", "").replace("```", "").strip()
    print("GPT 生成的夜盤代碼：\n", night_cleaned_code)
    
    night_context = {}
    success, result = execute_crawler_code(night_cleaned_code, night_context)
    print("執行結果：", result)
    
    # 檢查結果是否成功
    if not success:
        print("進入錯誤的success state:")
        print(f"錯誤訊息：\n{result}")
        user_feedback = input("請提供改進代碼的反饋：\n")
        crawl_and_merge_data(date, feedback=f"夜盤Code:\n{night_cleaned_code}\n夜盤錯誤輸出:\n{result}\n反饋：{user_feedback}")
        return
    else:
        # 顯示結果並詢問使用者是否符合預期
        night_data = night_context.get("night_data", pd.DataFrame())
        print("夜盤數據：\n", night_data)
        
        user_feedback = input("夜盤數據是否符合預期？(Yes/No/其他輸入):\n")
        
        if user_feedback.lower() == "yes":
            # 如果使用者輸入 Yes，則繼續執行後續步驟
            print("數據符合預期，繼續執行...")
        elif user_feedback.lower() == "no":
            # 如果使用者輸入 No，則重新生成代碼
            print("數據不符合預期，正在生成新的爬蟲代碼...")
            crawl_and_merge_data(date, feedback=f"夜盤Code:\n{night_cleaned_code}\n夜盤錯誤輸出:\n{result}\n反饋：數據不符合預期")
            return
        else:
            # 如果使用者輸入其他內容，請提供具體反饋並將反饋傳送給 GPT
            crawl_and_merge_data(date, feedback=f"夜盤Code:\n{night_cleaned_code}\n夜盤錯誤輸出:\n{result}\n反饋：{user_feedback}")
            return
#-----------------------------------------------------------
    if day_data.empty and night_data.empty:
        print("數據抓取失敗，請檢查代碼和來源！")
        crawl_and_merge_data(date, f"日盤Code:\n{day_cleaned_code}\n夜盤Code:\n{night_cleaned_code}\n錯誤輸出：數據為空！")
        return

    # 合併數據
    merged_data = pd.concat([day_data, night_data], ignore_index=True)

    # 指定所需的欄位
    day_columns = ["日期", "自營商多", "自營商空", "自營商多空淨額", "投信多", "投信空", "投信多空淨額", "外資多", "外資空", "外資多空淨額"]
    night_columns = ["日期", "多", "空", "多空淨額"]

    # 確保欄位存在
    merged_data = merged_data[day_columns + night_columns] if all(col in merged_data.columns for col in day_columns + night_columns) else merged_data
    print("merged_data:", merged_data)

    # 輸出為 Excel 檔案
    output_file = f"taiwan_futures_{date}.xlsx"
    merged_data.to_excel(output_file, index=False)
    print(f"數據已保存至 {output_file}")

if __name__ == "__main__":
    # 指定目標日期
    target_date = "2024/02/29"
    crawl_and_merge_data(target_date)
