from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import SecretStr
from app.config import settings

def translate_to_jeju(text):
    """
    제주 방언 번역기

    Args:
        text: 번역할 문장

    Returns:
        str: 제주 방언으로 번역된 문장
    """
    llm = ChatOpenAI(
        api_key=SecretStr(settings.openai_api_key),
        model=settings.openai_model,
        temperature=settings.openai_temperature
    )

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

    jeju_chain = prompt_template | llm | StrOutputParser()

    return jeju_chain.invoke({"text": text})


async def translate_to_jeju_async(text: str) -> str:
    """
    제주어 번역 (비동기 래퍼)

    동기 함수인 translate_to_jeju()를 asyncio.to_thread()로 래핑하여
    async 컨텍스트에서 안전하게 호출할 수 있도록 합니다.

    Args:
        text: 번역할 문장

    Returns:
        str: 제주어로 번역된 문장
    """
    import asyncio
    return await asyncio.to_thread(translate_to_jeju, text)
