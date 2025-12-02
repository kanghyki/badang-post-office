import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained("Junhoee/Kobart-Jeju-translation")
model = AutoModelForSeq2SeqLM.from_pretrained("Junhoee/Kobart-Jeju-translation").to(device)

def translate_jeju(input_string):
    input_string = "[표준] " + input_string
    input_ids = tokenizer(input_string, return_tensors="pt", padding=True, truncation=True).input_ids.to(device)
    outputs = model.generate(input_ids, max_length=64)
    decoded_output = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return decoded_output

# input_text = input("텍스트 입력: ")
# translated = translate_jeju(input_text)
# print(translated)
#
# for _ in range(10):
#     print(translate_jeju("안녕하세요"))