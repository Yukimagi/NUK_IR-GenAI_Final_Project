"""
**需求套件**
pip install langchain               # 用於文檔處理、嵌入模型和文本切割
pip install together               # Together API 客戶端
pip install sentence-transformers  # 嵌入處理（向量檢索）
pip install PyMuPDF                # 處理 PDF 文件
pip install numpy                  # 數據處理
pip install google-generativeai    # Google 生成式 AI 客戶端
pip install transformers           # Transformer 模型相關工具（如果需要其他嵌入模型）
pip install jieba                  # 分詞工具（若後續需要中文文本分詞）
pip install pip install -U langchain-community
"""
import logging

from langchain.document_loaders import PyMuPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import InMemoryVectorStore
from langchain.schema.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from google.generativeai.types import HarmBlockThreshold
from google.ai.generativelanguage_v1 import HarmCategory

from together import Together
import os
from dotenv import load_dotenv
import subprocess

import sys
# Set up logging
logging.basicConfig(filename='app_log.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


os.environ["GOOGLE_API_KEY"] = "AIzaSyAaQ8WdoHUV2K07H8h_O6dom5lDR0vHb4o"
# 載入 .env 文件
load_dotenv()

# 初始化嵌入模型和向量存儲
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vector_store = InMemoryVectorStore(embeddings)


def RAG(user_prompt):
    """
    Generate a story based on the user's prompt using Together API and retrieved content from PDFs.
    
    :param user_prompt: str, The user's prompt for the story.
    :param modelType: str, The Together AI model to use for generation.
    :return: str, The generated story.
    """
    system_prompt = """
            你會從參考資料中檢查題目與程式，並達成如下:

            請幫我撰寫一個 Python 程式(不准說明，只能撰寫python程式)，用來爬取台灣期貨交易所日盤與夜盤的期貨交易數據，並保存到 Excel 文件。程式需求如下：

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
    """
    logging.info("Starting PDF loading and processing.")
    # 獲取當前路徑
    current_path = os.getcwd()
    pdf_files = ["Prob1/hw2.pdf","Prob1/日.pdf","Prob1/夜.pdf"]

    # 加載和處理 PDF 文件
    for pdf_file in pdf_files:
        pdf_path = os.path.join(current_path, pdf_file)
        pdf_content = PyMuPDFLoader(pdf_path).load()
        logging.info(f"Successfully loaded PDF: {pdf_file}")
        # 文本切分
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        split_content = text_splitter.split_documents(pdf_content)

        # 將分割的文本加入向量存儲
        vector_store.add_documents(documents=split_content)

    # 基於用戶輸入進行檢索
    retrieved_docs = vector_store.similarity_search(user_prompt)
    retrieved_content = ""
    logging.info(f"Searching for relevant content based on user prompt: {user_prompt}")
    # 合併檢索到的內容
    for retrieved_doc in retrieved_docs:
        retrieved_content += retrieved_doc.page_content

    # 如果檢索內容為空，返回提示
    if not retrieved_content.strip():
        logging.warning("No relevant content found.")
        return "無法檢索到相關內容，請提供更具體的提示。"

    # 整理為 Together API 的 messages 格式
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": f"這是參考資料：\n{retrieved_content}"},
    ]
    logging.info("Calling API to generate response.")

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
    # 使用 Together API 生成回應
    try:
        response = ChatGoogleGenerativeAI(
            google_api_key=google_api_key,
            model=model,
            temperature=temperature,
            top_p=top_p,
            seed=seed,
            safety_settings=safety_settings
        )
        ans=response.invoke(messages)
        logging.info("Successfully generated response.")
        return ans.content
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return f"Error generating response: {e}"

# 定義函數來檢查程式碼執行結果
def execute_python_code(code):
    try:
        # 將生成的程式碼保存到檔案
        with open("generated_code.py", "w", encoding="utf-8") as f:
            f.write("# -*- coding: utf-8 -*-\n" + code)
        logging.info("Executing generated Python code.")
        # 執行該程式碼並捕獲輸出
        result = subprocess.run(
            ["python", "generated_code.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            if "error" in result.stdout:
                print("發現內部錯誤訊息，判定執行失敗：")
                logging.error("Internal error detected, execution failed.")
                return False, result.stdout
            print("程式執行成功！輸出如下：")
            print(result.stdout)
            if input("請檢查正確或錯誤(輸入正確/錯誤)")=="錯誤":
                logging.error("Internal error detected, execution failed.")
                return False, "錯誤"
            logging.info("Program executed successfully. Output:\n" + result.stdout)
            return True, result.stdout
        else:
            print("程式執行失敗，錯誤如下：")
            print(result.stderr)
            logging.error(f"Program execution failed. Error:\n{result.stderr}")
            return False, result.stderr
    except Exception as e:
        print("執行程式時發生例外：", str(e))
        logging.error(f"Exception during execution: {e}")
        
        return False, str(e)

success = False
msg=""
msg2=""
generated_code=""
i=0
# 測試函數
if __name__ == "__main__":
    while not success:
        print("正在透過 Gemini 生成程式碼...")
        
        oricode = RAG(msg2)
        generated_code = oricode.replace("```python", "").replace("```", "").strip()
        print("生成的程式碼如下：\n", generated_code)
        logging.info(f"Generated code:\n{generated_code}")
        # 嘗試執行生成的程式碼
        success,msg = execute_python_code(generated_code)
        if not success:
            i+=1
            print("程式執行失敗，重新生成程式碼...\n")
            if(i>10):
                print("請輸入多行內容，並按 Ctrl+D (Windows：Ctrl+Z) 結束:")
                msg2=sys.stdin.read()
            else:
                msg2=f"以下是之前的錯誤訊息:{msg}\n以下是之前產生的code\n{generated_code}"
            logging.warning("Program execution failed, regenerating code...")
        else:
            print("成功執行程式！")
            logging.info("Program executed successfully.")
