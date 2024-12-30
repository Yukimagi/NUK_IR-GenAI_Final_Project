"""
**需求套件**
pip install sentence-transformers
pip install torch
pip install transformers numpy scikit-learn
pip install jieba #分詞工具

**Sentence-BERT 模型**
基於 BERT 的變體，專門用於生成句子級的向量表示，並可用於計算句子之間的相似度。
該模型能夠高效地捕捉語義信息，並在多語言任務中表現優異。這使得它非常適合用於中文故事的評估。

**評分指標**
函數返回的結果包含三個主要評分指標：

    Coherence：故事與提示文本的語義一致性，通過計算餘弦相似度評估。
    Creativity：故事的詞彙多樣性，通過計算 Type-Token Ratio (TTR) 評估。
    Relevance：故事與參考文本的相關性，通過計算餘弦相似度評估（若提供 reference_text）。

"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import jieba  # 引入 jieba 分詞工具
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


def evaluate_story(
    content,
    prompt,
    reference_text,
    model_name="paraphrase-multilingual-MiniLM-L12-v2",
):
    """
    評估故事文本
    :param content: 已生成的文本
    :param prompt: 提示文本，用來判斷相關性。(文本是否與參考文本或主題保持一致，並且提供有效的回應或信息。)
    :param reference_text: 參考文本 (可選)
    :param model_name: Sentence-BERT 模型名稱 (默認為 all-MiniLM-L6-v2)
    :return: 字典，包含故事 ID 和評估結果
    """
    # 初始化 Sentence-BERT 模型
    model = SentenceTransformer(model_name)

    # 計算餘弦相似度（Cosine Similarity）
    def calculate_similarity(text1, text2):
        embeddings = model.encode([text1, text2])
        return cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

    # 計算詞彙多樣性 -Type-Token Ratio, TTR
    def calculate_diversity(text):
        # 使用 jieba 進行中文分詞
        words = jieba.cut(text)
        words_list = list(words)  # jieba.cut 返回的是生成器，需要轉換為 list
        unique_words = set(words_list)  # 去除重複的詞
        return len(unique_words) / len(words_list) if words_list else 0

    # 連貫與一致性評分 (與 prompt 的相似度)
    coherence = calculate_similarity(prompt, content)

    # 創意性評分 (詞彙多樣性)
    creativity = calculate_diversity(content)

    # 相關性評分 (與參考文本的相似度, 若有)
    relevance = calculate_similarity(reference_text, content)  #

    # 返回包含 ID 和評估結果的字典
    return {
        "scores": {
            "Coherence": round(coherence, 4),
            "Creativity": round(creativity, 4),
            "Relevance": round(relevance, 4) ,
        },
    }


# 測試使用
if __name__ == "__main__":
    # 測試數據
    prompt = "請給我一段關於健康的故事。"
    content = """
    小晴是一位在都市裡工作的年輕人，每天忙於應付工作壓力，過著作息不規律、飲食隨便的生活。早餐常常被忽略，午餐則以速食解決，晚餐則是宵夜和外賣的組合。這樣的生活方式讓她的健康狀況逐漸惡化。
    一天，她在下班途中突然感到頭暈目眩，被送往醫院急診後，醫生告訴她，長期缺乏運動和不健康的飲食導致了她的低血糖和高血壓問題。這次事件成了小晴的警鐘。
    出院後，她下定決心改變自己的生活方式。她開始學習如何規劃均衡的飲食，每天為自己準備富含營養的餐點，告別了高糖、高脂的外賣。為了改善身體狀況，她養成了每天清晨跑步的習慣，並報名參加了瑜伽課程，讓自己在忙碌中找到放鬆的時間。
    改變並不是一蹴而就的，但小晴一步一步地堅持下來。三個月後，她的體力和精神都明顯提升了，體重也恢復到健康範圍。醫生的複診報告顯示，她的血壓已經穩定，低血糖的情況也得到了改善。
    小晴感慨地說：「健康是生命的基石，沒有了健康，再多的努力和成就也失去了意義。」
    從此以後，小晴不僅保持著健康的生活方式，還影響了周圍的朋友和同事，一起加入了健康生活的行列。他們定期舉辦團隊跑步活動，交換健康食譜，讓健康不再是個人的選擇，而成為了一種生活態度。
    """
    reference_text = None

    result = evaluate_story(content, prompt)
    print("評分結果:", result)


""" test result
評分結果: {'scores': {'Coherence': 0.4191, 'Creativity': 0.5214, 'Relevance': 0.4191}}
"""
