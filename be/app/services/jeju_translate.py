# 1️⃣ 설치
# !pip install --upgrade openai langchain

# 2️⃣ 임포트 (최신 방식)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 3️⃣ LLM 객체 생성
llm = ChatOpenAI(
    openai_api_key="sk-여기에_본인_API_KEY",  # TODO: 자신의 OpenAI API 키
    model_name="gpt-5",  # GPT-4도 가능
    temperature=0.7
)

# 4️⃣ 프롬프트 템플릿
prompt_template = ChatPromptTemplate.from_messages([
    ("system", """You are an expert translator of Jeju dialect. 
Translate the following sentence into natural Jeju dialect."""),
    ("user", """Requirements:
1. Preserve the original meaning as much as possible.
2. Use expressions and tone actually used in Jeju.
3. Apply Jeju-style particles and endings appropriately.
4. Only output the translated sentence, do not add explanations.
Sentence: "{text}""")
])

# 5️⃣ LLMChain 생성
jeju_chain = prompt_template | llm | StrOutputParser()


# 6️⃣ 번역 함수
def translate_to_jeju(text):
    return jeju_chain.invoke({"text":text})

# 7️⃣ 테스트
text_to_translate = "안녕하세요, 오늘 날씨가 좋네요!"
result = translate_to_jeju(text_to_translate)

print(result)
