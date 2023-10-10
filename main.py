import streamlit as st
import json
import openai
import os
from dotenv import load_dotenv
import meilisearch
import pandas as pd

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")  # OpenAIのAPIキーを設定します。
meili_search_key =os.getenv("MEILI_SEARCHONLY_KEY") # meilisearch検索キーを設定します。
meili_url =os.getenv("MEILI_URL") # meilisearchへのURLを設定します。

def init_page():
    st.set_page_config(
        page_title="Database Search",
        page_icon="🤗",
        layout="wide",
        initial_sidebar_state="auto", 
        menu_items={
         'Get Help': 'https://www.google.com',
         'Report a bug': "https://www.google.com",
         'About': """
         # Database Search
         登録されたデータベースから検索し、AIに解説させます。
         """
     }
    )
    st.sidebar.title("DB選択")
    
    
def select_db():
    model = st.sidebar.radio("選択したDBから検索します:", 
    ( "ISMS系", "認定系", "全データ"),captions = ["27000,27001,27002検索", "17021,27006,一部のMD検索", "すべてのデータから検索"])
    if model == "ISMS系":
        st.session_state.db_name = "isms"
    elif model == "認定系":
        st.session_state.db_name = "accreditation"
    else:
        st.session_state.db_name = "data"
    #st.sidebar.write(st.session_state.db_name) #データ確認用

def get_keyword_call(searchword):
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
    {"role": "system", "content": "入力された文のキーワードのみを抽出し結果のみを表示せよ。結果は半角スペースで区切ること。"},
    {"role": "user", "content": searchword}
  ])
    
    keyword = completion.choices[0].message.content
    return keyword
    

def meilisearch_call(searchword):
    client = meilisearch.Client(meili_url, meili_search_key)
    search_result = client.index(st.session_state.db_name).search(searchword, {
  'limit': 5,
  'attributesToSearchOn': ['standard','clause','title', 'content_ja','keyword'],
  'attributesToRetrieve': ['standard','clause','title', 'content_ja'],
  #'attributesToHighlight': ['clause','title','content_ja'],
  #'highlightPreTag': '<span class="highlight">',
  #'highlightPostTag': '</span>',
  #'filter': [['category = ISO', 'category_sub = ISMS'], 'standard = "ISO 27001"'],
  'showRankingScore': True})

    df =pd.DataFrame(search_result) #dataframeにインプット

    df =df.drop(['query','processingTimeMs','estimatedTotalHits','limit','offset'], axis=1) #いらない列を消去
    s = df.stack() # hits順に並び替え
    df=pd.json_normalize(s) #ノーマライズ
    return df


def main():
    init_page()

    st.title("Database Search")
    select_db() #サイドバーでの選択肢

    searchword = st.text_input('**検索内容を入力:**', "", placeholder="脅威インテリジェンスとは?")
    if not searchword: #空欄の場合の判定
        st.warning('検索内容を入力してください。')
        st.stop()
    
    st.divider()

    try:
        keyword_result = get_keyword_call(searchword)
        #st.write(keyword_result)
    
        meili_search_result = meilisearch_call(keyword_result)
        st.write('**DB一致内容:**')
        st.dataframe(meili_search_result, 
                 column_config={
                     "standard": "規格",
                     "clause": "箇条",
                     "title": "表題",
                     "clause": "箇条",
                     "content_ja": "内容",
                     "_rankingScore": "一致率",
                     },
                     hide_index=True,
                     )
    except Exception as e:
        st.write(f"Error:{str(e)}")
        
    st.divider()

    json_str = meili_search_result.to_json()
    data = json.loads(json_str) #デシリアライズがおかしい?一応いけているが…
    #st.write(data) #データ確認用

    st.write("**AI解説:**")
    message_placeholder = st.empty()
    full_response = ""

    for completion2 in openai.ChatCompletion.create(
    model="gpt-3.5-turbo-16k", 
    messages=[
    {"role": "system", "content": "あなたは「ISOの専門家」です。userからの質問に答えるために、以下の制約条件から最高の要約を出力してください。"},
    {"role": "user", "content": f"""
     #命令書:
     入力データから、「{searchword}」という質問の目的を考慮し、関連性の低い部分は削除すること。
     質問に対して関連性が高い部分を整理し、重要なキーワードを含めて論理的に段階的わかりやすくまとめること。
     初めに質問に関する用語定義を示し、その後に関連する要求事項及び管理策を説明すること
        
     #制約条件:
     要件という言葉は要求事項と置き換えて記述すること
     入力データにのっていないことは「データにありません。」と返答すること
     入力データの内容のみを利用し、要約をまとめること
     文章は500文字程度で、簡潔に記述すること
     出力例の形式にあわせて出力すること
     ですます調にてまとめること

     #入力データ:
     {data}

     #出力例:
     以下がご質問に関する解説となります。
     ISO/IEC 27001の用語定義は、「情報セキュリティ、サイバーセキュリティ及びプライバシー保護に関する情報セキュリティマネジメントシステムの要求事項」です。
     組織にて情報セキュリティマネジメントシステムを構築するために利用することができます。
     

"""}
  ],
  temperature = 0.2,
  stream=True
):
        full_response += completion2.choices[0].delta.get("content", "")
        message_placeholder.markdown(full_response + " ")
    
    message_placeholder.markdown(full_response)



if __name__ == '__main__':
    main()
