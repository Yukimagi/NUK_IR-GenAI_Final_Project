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

from langchain.document_loaders import PyMuPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import InMemoryVectorStore
from together import Together
import os
from dotenv import load_dotenv

os.environ["GOOGLE_API_KEY"] = "AIzaSyAaQ8WdoHUV2K07H8h_O6dom5lDR0vHb4o"
# 載入 .env 文件
load_dotenv()
# Together API Client 初始化
together_client = Together(api_key=os.environ.get("TOGETHER_API_KEY3"))

# 初始化嵌入模型和向量存儲
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vector_store = InMemoryVectorStore(embeddings)


def StoryRAG(user_prompt, modelType):
    """
    Generate a story based on the user's prompt using Together API and retrieved content from PDFs.
    
    :param user_prompt: str, The user's prompt for the story.
    :param modelType: str, The Together AI model to use for generation.
    :return: str, The generated story.
    """
    system_prompt = """
    你是一個專業的新聞說故事小幫手，
    你的目標是根據retrieved_content的新聞內容，產生故事，但不行偏離參考新聞資料。
    """

    # 獲取當前路徑
    current_path = os.getcwd()
    pdf_files = ["rag_data/Stock.pdf","rag_data/Sport.pdf","rag_data/Health.pdf"]

    # 加載和處理 PDF 文件
    for pdf_file in pdf_files:
        pdf_path = os.path.join(current_path, pdf_file)
        pdf_content = PyMuPDFLoader(pdf_path).load()

        # 文本切分
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        split_content = text_splitter.split_documents(pdf_content)

        # 將分割的文本加入向量存儲
        vector_store.add_documents(documents=split_content)

    # 基於用戶輸入進行檢索
    retrieved_docs = vector_store.similarity_search(user_prompt)
    retrieved_content = ""

    # 合併檢索到的內容
    for retrieved_doc in retrieved_docs:
        retrieved_content += retrieved_doc.page_content

    # 如果檢索內容為空，返回提示
    if not retrieved_content.strip():
        return "無法檢索到相關內容，請提供更具體的提示。"

    # 整理為 Together API 的 messages 格式
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": f"這是參考新聞資料：\n{retrieved_content}"},
    ]

    # 使用 Together API 生成回應
    try:
        response = together_client.chat.completions.create(
            model=modelType,
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {e}"



# 測試函數
if __name__ == "__main__":
    user_prompt = "請生成一個關於運動員的故事"
    modelType = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    story = StoryRAG(user_prompt, modelType)
    print("Generated Story: ///////////////////////////////////////////////")
    print(story)
