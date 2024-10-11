import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Load the model and tokenizer
model_name = "roberta-base-openai-detector"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

def detect_ai_generated_text(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        predicted_class = torch.argmax(logits, dim=1).item()
        confidence = torch.softmax(logits, dim=1).max().item()  # Get confidence score

    return {
        "result": "AI-generated" if predicted_class == 1 else "Human-written",
        "confidence": confidence
    }

def ai_detection(text: str) -> (float, float):
    result = detect_ai_generated_text(text)
    confidence = result['confidence']
    
    ai_percentage = confidence * 100  
    human_percentage = 100 - ai_percentage 
    return ai_percentage, human_percentage

def humaniser(text: str) -> (str, float, float):
   
    humanized_text = text.replace("AI-generated", "crafted by a human")  
    humanized_text = humanized_text.replace("generated", "created")

    ai_keywords = ["AI", "generated", "automatic", "machine"]
    human_keywords = ["crafted", "written", "created by a human", "unique"]

    ai_count = sum(humanized_text.count(keyword) for keyword in ai_keywords)
    human_count = sum(humanized_text.count(keyword) for keyword in human_keywords)

    total_count = ai_count + human_count
    if total_count > 0:
        ai_percentage_after_humanization = (ai_count / total_count) * 100
        human_percentage_after_humanization = (human_count / total_count) * 100
    else:
        ai_percentage_after_humanization = 0.0
        human_percentage_after_humanization = 100.0

    return humanized_text, ai_percentage_after_humanization, human_percentage_after_humanization

