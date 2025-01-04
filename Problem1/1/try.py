from together import Together
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import re
import streamlit as st

# Together API 初始化
client = Together(api_key="58fd39cddd733f466f8343fd61d86b9d020639b2951a9f17963dd76ac9627978")

def extract_query_details(user_input):
    """從使用者輸入中提取起始日期、結束日期和查詢項目"""
    prompt = f"""
        從以下輸入中提取細節：
        1. 找出起始日期（`start_date`）和結束日期（`end_date`），格式為 YYYY/MM/DD。
        - 起始日期為輸入中提到的最早日期。
        - 結束日期為輸入中提到的最晚日期，若未提到則默認為今天的日期。
        2. 找出輸入中提到的查詢項目（例如：「外資多單」、「自營商淨多單」）。

        範例輸入：
        「從 2024/12/01 到 2024/12/15，取得外資多單的未平倉數據。」

        期望的輸出格式：
        start_date:2024/12/01
        end_date:2024/12/15
        data:[外資多單]

        輸入: {user_input}

        請按照上述格式輸出結果(並且不要做多餘的解釋)：
    """
    response = client.chat.completions.create(
        model="Qwen/QwQ-32B-Preview",
        messages=[{"role": "system", "content": "你是一個超級聰明的助手。"},
                  {"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.7,
        top_p=0.7,
        top_k=50,
        repetition_penalty=1,
        stop=["<|im_end|>", "<|endoftext|>"]
    )
    
    output = response.choices[0].message.content.strip()
    print("提取的輸出:", output)

    # 使用正則表達式解析日期與項目
    details = {
        'start_date': None,
        'end_date': None,
        'data': []
    }
    try:
        details['start_date'] = re.search(r"start_date:(\d{4}/\d{2}/\d{2})", output).group(1)
        details['end_date'] = re.search(r"end_date:(\d{4}/\d{2}/\d{2})", output).group(1)
        data_match = re.search(r"data:\[(.*?)\]", output)
        if data_match:
            details['data'] = data_match.group(1).split(", ")
    except AttributeError:
        print("解析失敗，回應格式可能不正確:", output)

    return details


# 使用者輸入
st.title("查詢期貨數據")

# 使用者輸入
user_input = st.text_input("請輸入查詢條件：")
#user_input = input("Enter your query: ")
try:
    query_details = extract_query_details(user_input)
    print("query_details:", query_details)
    st.success("提取的查詢細節：")
    st.json(query_details)
    if not query_details.get("start_date") or not query_details.get("data"):
        print("沒在prompt取得日期(query_details):", query_details)
        raise ValueError("Incomplete details from API")
except Exception as e:
    print("API parsing failed. Falling back to manual parsing.")
    #query_details = fallback_parse(user_input)

# 日期範圍
start_date = datetime.strptime(query_details['start_date'], "%Y/%m/%d")
end_date = datetime.strptime(query_details['end_date'], "%Y/%m/%d")
print("Parsed Query Details:", query_details)

# 初始化變量
url = "https://www.taifex.com.tw/cht/3/futContractsDate"
url_night = "https://www.taifex.com.tw/cht/3/futContractsDateAh"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}
# 獲取當前腳本的路徑
current_dir = os.path.dirname(os.path.abspath(__file__))

# 檔案名
file_name = "test.xlsx"

# 建立完整的檔案路徑
file_path = os.path.join(current_dir, file_name)

file_exist=0 #初始設定檔案不存在
day_OR_night=0 #設上一筆存到日盤
# 儲存日盤和日盤+夜盤數據
data_list = []
# 遍歷日期範圍
delta = timedelta(days=1)
while start_date <= end_date:
    date_str = start_date.strftime("%Y/%m/%d")
    print(f"正在爬取 {date_str} 的資料...")

    # 抓取日盤數據
    form_data_day = {
        "queryDate": date_str,
        "commodityId": "TXF",
    }
    response_day = requests.post(url, headers=headers, data=form_data_day)
    soup_day = BeautifulSoup(response_day.content, "html.parser")
    
    # 抓取夜盤數據（隔天的夜盤）
    next_date = start_date + delta
    next_date_str = next_date.strftime("%Y/%m/%d")
    form_data_night = {
        "queryDate": next_date_str,
        "commodityId": "TXF",
    }
    response_night = requests.post(url_night, headers=headers, data=form_data_night)
    soup_night = BeautifulSoup(response_night.content, "html.parser")
    
    # 處理日盤數據
    table_day = soup_day.find("table", {"class": "table_f"})
    table_night = soup_night.find("table", {"class": "table_f"})

    data_D, data_G, data_J = None, None, None  # 初始化變量###
    if table_day:
        rows_day = table_day.find_all("tr")
        
        if len(rows_day) > 2:
            data_B = rows_day[3].find_all("td", {"align": "right"})[6].text.strip()
            data_C = rows_day[3].find_all("td", {"align": "right"})[8].text.strip()
            data_D = rows_day[3].find_all("td", {"align": "right"})[10].text.strip()

            data_E = rows_day[4].find_all("td", {"align": "right"})[6].text.strip()
            data_F = rows_day[4].find_all("td", {"align": "right"})[8].text.strip()
            data_G = rows_day[4].find_all("td", {"align": "right"})[10].text.strip()

            data_H = rows_day[5].find_all("td", {"align": "right"})[6].text.strip()
            data_I = rows_day[5].find_all("td", {"align": "right"})[8].text.strip()
            data_J = rows_day[5].find_all("td", {"align": "right"})[10].text.strip()
            
            # 將日盤數據存入 data_list
            data_list.append([date_str, data_B, data_C, data_D, data_E, data_F, data_G, data_H, data_I, data_J])
    
    # 處理夜盤數據，如果夜盤沒開盤則跳過
    if table_night:
        rows_night = table_night.find_all("tr")
        
        if len(rows_night) > 2:
            # 抓取夜盤數據
            data_D_night = rows_night[3].find_all("td", {"align": "right"})[4].text.strip()
            data_G_night = rows_night[4].find_all("td", {"align": "right"})[4].text.strip()
            data_J_night = rows_night[5].find_all("td", {"align": "right"})[4].text.strip()
            
            # 處理日盤與夜盤相加的邏輯 (只相加 D, G, J)
            try:
                data_D_combined = str(int(data_D.replace(",", "")) + int(data_D_night.replace(",", ""))) if data_D else data_D_night
            except ValueError:
                data_D_combined = data_D  # 若非數字則保持原樣

            try:
                data_G_combined = str(int(data_G.replace(",", "")) + int(data_G_night.replace(",", ""))) if data_G else data_G_night
            except ValueError:
                data_G_combined = data_G

            try:
                data_J_combined = str(int(data_J.replace(",", "")) + int(data_J_night.replace(",", ""))) if data_J else data_J_night
            except ValueError:
                data_J_combined = data_J
            
            # 將日盤 + 夜盤數據存入 data_list，日期與上方相同
            data_list.append([next_date_str, "", "", data_D_combined, "", "", data_G_combined, "", "", data_J_combined])
    
    start_date += delta

if (file_exist == 1) and(day_OR_night==0):
    # 刪除 data_list 中的第一筆日盤資料（即陣列中的第一筆）
    if data_list:  # 確保 data_list 不為空
        data_list.pop(0)
        
# 檢查文件是否存在
if os.path.exists(file_path):
    # 如果文件存在，先清空文件
    print(f"文件 {file_name} 已存在，正在清空文件內容...")
    os.remove(file_path)

# 創建新的 DataFrame 並保存數據
df_combined = pd.DataFrame(data_list, columns=["DATE", "自營商多", "自營商空", "自營商多空淨額", "投信多", "投信空", "投信多空淨額", "外資多", "外資空", "外資多空淨額"])
df_combined.to_excel(file_path, index=False)

print(f"數據已成功保存到 {file_path}")


# 從 Excel 檔案中匹配數據並打印
if os.path.exists(file_path):
    # 讀取 Excel 檔案
    df_existing = pd.read_excel(file_path)
    
    # 查詢的數據項目
    query_columns = []
    
    query_columns.extend(query_details['data'])
    print("query columns：",query_columns)
    if query_columns:
        # 過濾出匹配的數據
        filtered_df = df_existing[["DATE"] + query_columns]
        print("\n匹配的數據如下:")
        print(filtered_df.to_markdown(index=False))  # 使用 Markdown 格式打印表格
        st.write("匹配的數據如下：")
        st.dataframe(filtered_df)
    else:
        print("\n沒有匹配的數據項目.")
else:
    print("\nExcel 檔案不存在，無法查詢數據.")

