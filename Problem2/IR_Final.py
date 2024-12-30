#streamlit run C:/Users/USER/Python_code/ir_genAI/IR_Final.py
from StoryRAG import StoryRAG

from nlp_sentenceBert import evaluate_story

import asyncio
from datetime import datetime, timedelta
from supabase import create_client, Client
from together import Together
import os
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import jieba
from dotenv import load_dotenv
import textwrap
import math
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
import google.generativeai as genai
from langchain.schema.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.document_loaders import PyMuPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import InMemoryVectorStore

from google.generativeai.types import HarmBlockThreshold
from google.ai.generativelanguage_v1 import HarmCategory
from IPython.display import display, Markdown
import json
import streamlit as st

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import base64
from io import BytesIO

import nest_asyncio
nest_asyncio.apply()


# Load environment variables
load_dotenv()

# Together API client
together_client = Together(api_key=os.environ.get("TOGETHER_API_KEY3"))

async def together_response(question, modelType):
    """
    Use Together API to generate a response.
    :param question: string Question command.
    :param modelType: string Model type.
    :return: string AI response.
    """
    messages = [{"role": "user", "content": f"問題:\n{question}\n\n回答:"}]
    try:
        response = together_client.chat.completions.create(
            model=modelType,
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error with Together API: {e}")
        return "exception"

async def together_response_mutate(question, modelType):
    """
    Use Together API to generate a mutated response.
    :param question: string Question command.
    :param modelType: string Model type.
    :return: string AI response.
    """
    messages = [{"role": "user", "content": f"變異這個指令內容，並保留語意：{question}\n只要回答變體的指令內容即可"}]
    try:
        response = together_client.chat.completions.create(
            model=modelType,
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error with Together API: {e}")
        return "exception"

async def chat_first(query,modelType):
    return await together_response(query, modelType)

async def chat_mutate(query,modelType):
    return await together_response_mutate(query, modelType)

def convert_float32_to_float(obj):
    if isinstance(obj, np.float32):
        return float(obj)  # 將 np.float32 轉換為 float
    elif isinstance(obj, dict):
        return {key: convert_float32_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_float32_to_float(item) for item in obj]
    else:
        return obj

def save_result_to_json(result, file_name):
    # 轉換 result 中的所有 np.float32 為 float
    result = convert_float32_to_float(result)
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)


def load_result_from_json(file_name):
    """Load result data from a JSON file."""
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

form_counter = 0
CURRENT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
def user(result):
    """
    Handle user interactions for evaluation and feedback.
    """
    global form_counter
    form_key = f"multiple_actions_form_{form_counter}"  # Create a unique key
    form_counter += 1

    with st.form(form_key):
        last_entry = result[-1]
        st.write(f"Prompt: {last_entry['prompt']}")
        st.write(f"Story: {last_entry['story']}")
        st.write(f"Score: {last_entry['score']}")
        
        st.write("請對故事進行評價：")
        st.session_state.feedback = st.text_input("請輸入您的反饋：")
        # 使用更細的步長，例如 0.05，讓使用者選擇 0 到 1 之間的值，包含 0.1、0.2、0.15 等
        st.session_state.user_score = st.slider("請為故事評分：", min_value=0.0, max_value=1.0, step=0.01)
        
        # 定義兩個按鈕
        generate_button = st.form_submit_button("產生結果")
        optimize_button = st.form_submit_button("繼續優化")

    if generate_button:  # 按下產生結果按鈕後執行
        # 處理產生結果的邏輯
                # 生成圖片
        last_entry = st.session_state.result[-1]
        response = together_client.images.generate(
            prompt=f"請依照以下的文章情節:\n{last_entry['story']}\n來生成對應的圖片，記得一定要符合故事的內容",
            model="black-forest-labs/FLUX.1-dev",
            width=1024,
            height=768,
            steps=28,
            n=1,
            response_format="b64_json"
        )

        # 取出 Base64 編碼的圖片數據
        b64_image = response.data[0].b64_json
        # 將 Base64 編碼的圖像轉換為圖片格式
        img_data = base64.b64decode(b64_image)
        img = BytesIO(img_data)

        # 顯示圖片
        st.image(img, caption="生成的圖片", use_column_width=True)
        
        #last_entry = st.session_state.result[-1]
        new_query = last_entry['prompt']
        #ans = asyncio.run(chat_first(new_query,st.session_state.modelType))
        #new_story = last_entry['story']
        result.append({"prompt": f'使用者最終結果:{new_query}', "story": last_entry['story'], "score": last_entry['score']})
        
        file_name = f"{CURRENT_DIR_PATH}/result_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        save_result_to_json(result, f'{file_name}.json')
        
        # 將 Base64 解碼並保存為圖片
        with open(f'{file_name}.png', "wb") as img_file:
            img_file.write(base64.b64decode(b64_image))

        st.write(f"圖片已成功生成並保存為 '{file_name}.png'")
        
        st.write(f"結果已保存到 {file_name}.json，請重新操作。")
        
    if optimize_button:  # 按下繼續優化按鈕後執行
        #st.session_state.feedback = feedback
        #st.session_state.user_score = user_score

        # 處理優化的邏輯
        ans = f"請參考使用者的回饋分數:{st.session_state.user_score} 和回饋評語:{st.session_state.feedback}，用以下 prompt {last_entry['prompt']} 繼續變異。"
        #ans = asyncio.run(chat_first(feedback_prompt,st.session_state.modelType))
        new_story = StoryRAG(ans,st.session_state.modelType)
        NLP_result = evaluate_story(new_story, ans,st.session_state.PDF)
        scores = NLP_result['scores']
        coherence = scores['Coherence']
        creativity = scores['Creativity']
        relevance = scores['Relevance']
        st.session_state.result.append({"prompt": ans, "story": new_story, "score": scores})
        st.write(f"正在「初始迭帶」優化prompt、生成內容與計算NLP分數...\ncoherence: {coherence}、creativity: {creativity}、relevance: {relevance}")
        
        while coherence < st.session_state.coh or creativity < st.session_state.cre or relevance < st.session_state.rel:
            
            ans = asyncio.run(chat_mutate(f'''請參考目前prompt所得文章分數
                                coherence:{coherence}(最終須大於{st.session_state.coh}) 、
                                creativity:{creativity}(最終須大於{st.session_state.cre})、
                                relevance:{relevance}(最終須大於{st.session_state.rel}) ，用以下 prompt{ans}繼續變異
                                      ''',st.session_state.modelType))
            
            new_story = StoryRAG(ans,st.session_state.modelType)
            NLP_result = evaluate_story(new_story, ans,st.session_state.PDF)
            scores = NLP_result['scores']
            coherence = scores['Coherence']
            creativity = scores['Creativity']
            relevance = scores['Relevance']
            st.session_state.result.append({"prompt": ans, "story": new_story, "score": scores})
            st.write(f"正在「繼續迭帶」優化prompt、生成內容與計算NLP分數...\ncoherence: {coherence}、creativity: {creativity}、relevance: {relevance}")
        
        st.write("優化完成！")
        user(result)
        
        
# 初始化 session_state
if 'result' not in st.session_state:
    st.session_state.result = []
if 'modelType' not in st.session_state:
    st.session_state.modelType = ""
if 'feedback' not in st.session_state:
    st.session_state.feedback = ""
if 'user_score' not in st.session_state:
    st.session_state.user_score = 0
if 'user_test' not in st.session_state:
    st.session_state.user_test = False
if "form_displayed" not in st.session_state:
    st.session_state["form_displayed"] = False  # 表單是否顯示
if 'PDF' not in st.session_state:
    st.session_state.PDF = ""
if 'coh' not in st.session_state:
    st.session_state.coh = 0
if 'cre' not in st.session_state:
    st.session_state.cre = 0
if 'rel' not in st.session_state:
    st.session_state.rel = 0


st.title("AI故事生成平台")
st.session_state.modelType = st.selectbox("選擇模型", ["meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo","Qwen/QwQ-32B-Preview","google/gemma-2-27b-it","microsoft/WizardLM-2-8x22B","togethercomputer/m2-bert-80M-32k-retrieval"])
theme = st.selectbox("選擇主題", ["STOCK", "HEALTH", "SPORT"])
genre = st.selectbox("選擇類型", ["短篇故事", "互動對話"])
tone = st.selectbox("選擇語氣", ["幽默", "正式", "悲傷"])
key_elements = st.text_input("輸入關鍵元素 (例如：角色, 地點)")
st.session_state.coh = st.slider("目標coherence：", min_value=0.0, max_value=1.0, step=0.05)
st.session_state.cre = st.slider("目標creativity：", min_value=0.0, max_value=1.0, step=0.05)
st.session_state.rel = st.slider("目標relevance：", min_value=0.0, max_value=1.0, step=0.05)

# 獲取當前路徑
current_path = os.getcwd()
pdf_files = ["rag_data/Stock.pdf","rag_data/Sport.pdf","rag_data/Health.pdf"]

if theme=="STOCK":
    pdf_path = os.path.join(current_path, pdf_files[0])
    st.session_state.PDF = str(PyMuPDFLoader(pdf_path).load())
elif theme=="SPORT":
    pdf_path = os.path.join(current_path, pdf_files[1])
    st.session_state.PDF = str(PyMuPDFLoader(pdf_path).load())
elif theme=="HEALTH":
    pdf_path = os.path.join(current_path, pdf_files[2])
    st.session_state.PDF = str(PyMuPDFLoader(pdf_path).load())

if st.button("生成故事"):
    ans = f"請用主題:{theme}、類型:{genre}、語氣:{tone}、關鍵元素:{key_elements}，以上的元素生成一個prompt可以讓大語言模型生成好的對應回覆"
    #ans = asyncio.run(chat_first(prompt,st.session_state.modelType))
    story = StoryRAG(ans,st.session_state.modelType)
    NLP_result = evaluate_story(story, ans,st.session_state.PDF)
    scores = NLP_result['scores']
    coherence = scores['Coherence']
    creativity = scores['Creativity']
    relevance = scores['Relevance']
    st.session_state.result.append({"prompt": ans, "story": story, "score": scores})
    st.write(f"正在「開始」優化prompt、生成內容與計算NLP分數...\ncoherence: {coherence}、creativity: {creativity}、relevance: {relevance}")
    
    while coherence < st.session_state.coh or creativity < st.session_state.cre or relevance < st.session_state.rel:
        ans = asyncio.run(chat_mutate(f'''請參考目前prompt所得文章分數
                                      coherence:{coherence}(最終須大於{st.session_state.coh}) 、
                                      creativity:{creativity}(最終須大於{st.session_state.cre})、
                                      relevance:{relevance}(最終須大於{st.session_state.rel}) ，用以下 prompt{ans}繼續變異
                                      ''',st.session_state.modelType))
        
        story = StoryRAG(ans,st.session_state.modelType)
        NLP_result = evaluate_story(story, ans,st.session_state.PDF)
        scores = NLP_result['scores']
        coherence = scores['Coherence']
        creativity = scores['Creativity']
        relevance = scores['Relevance']
        st.session_state.result.append({"prompt": ans, "story": story, "score": scores})
        st.write(f"正在「迭帶」優化prompt、生成內容與計算NLP分數...\ncoherence: {coherence}、creativity: {creativity}、relevance: {relevance}")
    #user_test=False    
    st.write("優化完成！")
    
    st.session_state["form_displayed"] = True
    # 評價部分用 st.form 包裝
if st.session_state["form_displayed"]:
    user(st.session_state.result)
    

