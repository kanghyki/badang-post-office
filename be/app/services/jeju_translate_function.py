# !pip install --upgrade openai langchain

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def translate_to_jeju(text, model_name="gpt-5-nano", temperature=0.7):
    """
    제주 할머니 느낌의 방언 번역기 (올인원 함수)

    text: 번역할 문장
    model_name: 기본 gpt-5-nano
    """

    OPENAI_API_KEY = "sk-여기에_실_API_KEY_넣기"

    # 1️⃣ LLM 객체 생성
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY, # TODO: 자신의 OpenAI API 키
        model_name=model_name,
        temperature=temperature
    )

    # 2️⃣ 프롬프트 템플릿
    prompt_template = ChatPromptTemplate.from_messages([
        ("system",
         "You are an expert translator  who speaks like an elderly Jeju grandmother. "
         "Translate the following sentence into warm, natural, traditional Jeju dialect."
         ),
        ("user",
         """Requirements:
1. Preserve the original meaning as much as possible.
2. Use expressions and tone actually used in Jeju and by elderly Jeju grandmothers.
3. Use Jeju particles and endings naturally (e.g., -주게, -수다, -마씸, -하주게, -허우꽈, -앙/어영,-졍/쪄 등).
4. Make the tone warm and soft.
5. Apply Jeju-style particles and endings appropriately.
6. Only output the translated sentence, do not add explanations.
Sentence: "{text}" """
         )
    ])

    # 3️⃣ 체인 구성
    jeju_chain = prompt_template | llm | StrOutputParser()

    # 4️⃣ 실행 및 결과 반환
    return jeju_chain.invoke({"text": text})