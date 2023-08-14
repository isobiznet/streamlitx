#https://docs.streamlit.io/knowledge-base/using-streamlit/retrieve-filename-uploaded
#https://andymcdonaldgeo.medium.com/uploading-and-reading-files-with-streamlit-92885ac3a1b6 st.fileuploaderの詳細説明

import streamlit as st
import pandas as pd
import os
import openai
from pathlib import Path
import random, string
from pypdf import PdfReader
from dotenv import load_dotenv
#----------------------DEF------------------------

#random生成-フォルダをわけないならいらないかも
def randomname(n):
   return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

# テキストの抽出関数
def extract_text(reader):
    loaded_text=""
    number_of_pages = len(reader.pages)# ページ数の取得
    for texts in range(number_of_pages):
        page = reader.pages[texts]
        text = page.extract_text()
        loaded_text ="".join((loaded_text,text))
    
    return loaded_text #結果を返す
 
def chatgpt(query,add_prompt,data):
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")  # OpenAIのAPIキーを設定します。
    
    # GPT-3.5-turbo-16kを使用してテキストを整形
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo-16k",#やっぱgpt-4の方が精度が高い
      temperature = 1,
      #max_tokens =15000,
      stream = False,
      messages=[
            {"role": "system", "content": f"""以下のデータをもとに回答してください。データに該当しない場合は「データに該当無し」と答えてください。{add_prompt}#データ:{data}"""},
            {"role": "user", "content": query},
        ]
    )

    return response['choices'][0]['message']['content']
#----------------------DEF------------------------

#def main():にしたい。。。
uploaded_files=[]
FILES_PATH = "FILES"
os.makedirs(FILES_PATH, exist_ok=True) 
results = ""
   
uploaded_files = st.file_uploader("ファイルをUploadしてください:", type="PDF", accept_multiple_files=True)



if uploaded_files : #is not Noneはつけなくてもいい？
   for uploaded_file in uploaded_files:#一度ここで変数にいれないと.nameみたいなattributeが使えないみたい
      #ファイルへ保存
      file = os.path.join(FILES_PATH, uploaded_file.name)
      with open(file, 'wb') as f:
            f.write(uploaded_file.read()) 
       
      #PDFReader 
      loader = PdfReader(FILES_PATH +'/'+ uploaded_file.name)
      
      #テキストの抽出関数コール
      results = extract_text(loader)
      with st.expander("Loaded Dataを見る"):
         st.write(f"文字数:{len(results)}文字",results)

st.divider()
user_prompt = st.text_area("PROMPT:", value="Answer in japanese.")      
user_message = st.text_area("質問を以下に入力してください:")
submitted = st.button("質問する")

if submitted:
   if len(results) == 0:
       st.error("Loaded Dataがありません。")
       st.stop()
   if user_message == "":
       st.error("質問が入力されていません。")
       st.stop()
   answer = chatgpt(query=user_message,add_prompt=user_prompt,data=results)
   st.write(answer)   

