# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

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
file_name = "IR_Final_Prob1.xlsx"

# 建立完整的檔案路徑
file_path = os.path.join(current_dir, file_name)

file_exist=0#初始設定檔案不存在
day_OR_night=0#設上一筆存到日盤

if os.path.exists(file_path):
    # 如果檔案存在，從最新日期開始爬取
    df_existing = pd.read_excel(file_path)
    last_date_str = df_existing['DATE'].max()
    start_date = datetime.strptime(last_date_str, "%Y/%m/%d")
    file_exist=1
    if pd.isna(df_existing.iloc[-1, 1]):  # 檢查 DataFrame 是否為空或最後一行第一欄是否為空
        day_OR_night= 1
    print(f"檔案已存在，從最新日期 {last_date_str} 開始爬取")
else:
    # 如果檔案不存在，從三年前的今天開始爬取
    start_date = datetime.today() - timedelta(days=3*365)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = start_date #- timedelta(days=1)  # 確保從三年前的今天（10/25）開始
    print(f"檔案不存在，請檢查工作目錄：{os.getcwd()}，從三年前的今天開始爬取 {start_date.strftime('%Y/%m/%d')}")

# 爬取到今日的數據
end_date = datetime.today()

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

# 將新數據添加到已存在的 Excel 文件（如果存在）
if os.path.exists(file_path):
    df_existing = pd.read_excel(file_path)
    df_new = pd.DataFrame(data_list, columns=["DATE", "自營商多", "自營商空", "自營商多空淨額", "投信多", "投信空", "投信多空淨額", "外資多", "外資空", "外資多空淨額"])
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
else:
    df_combined = pd.DataFrame(data_list, columns=["DATE", "自營商多", "自營商空", "自營商多空淨額", "投信多", "投信空", "投信多空淨額", "外資多", "外資空", "外資多空淨額"])

# 保存 Excel
df_combined.to_excel(file_path, index=False)

print(f"數據已成功保存到 {file_path}")



# 讀取生成的 IR_Final_Prob1.xlsx 文件
df_ir_final = pd.read_excel(file_path)

# 讀取 hw2_A1105505.xlsx 文件（假設它存在並與 IR_Final_Prob1.xlsx 同一目錄中）
hw2_file_path = os.path.join(current_dir, "hw2_A1105505.xlsx")
df_hw2 = pd.read_excel(hw2_file_path)

# 过滤出 DATE 为 "2024/09/04" 的行
df_ir_final_filtered = df_ir_final[df_ir_final['DATE'] == '2024/09/04']
df_hw2_filtered = df_hw2[df_hw2['DATE'] == '2024/09/04']

# 確保兩個 DataFrame 都按列排序，這樣就不會受索引順序影響
df_ir_final_filtered_sorted = df_ir_final_filtered.sort_values(by=list(df_ir_final_filtered.columns)).reset_index(drop=True)
df_hw2_filtered_sorted = df_hw2_filtered.sort_values(by=list(df_hw2_filtered.columns)).reset_index(drop=True)

# 比較兩個表格的數據是否一致
if df_ir_final_filtered_sorted.equals(df_hw2_filtered_sorted):
    print("兩個文件的資料一致！")
else:
    print("兩個文件的資料不一致！")
    # 可以輸出不同的部分供進一步檢查
    comparison = df_ir_final_filtered_sorted.compare(df_hw2_filtered_sorted)
    print("差異：")
    print(comparison)

        

        