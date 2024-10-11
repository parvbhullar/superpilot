from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services import ai_detection, humaniser

app = FastAPI()

class TextInput(BaseModel):
    text: str

@app.post("/detect/")
async def detect_text(input: TextInput):
    try:
        ai_percentage, human_percentage = ai_detection(input.text)
        return {
            "AI_percentage": ai_percentage,
            "Human_percentage": human_percentage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/humanize/")
async def humanize_text(input: TextInput):
    try:
        humanized_text, ai_percentage, human_percentage = humaniser(input.text)
        return {
            "humanized_text": humanized_text,
            "AI_percentage_after_humanization": ai_percentage,
            "Human_percentage_after_humanization": human_percentage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
