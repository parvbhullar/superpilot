from superpilot.core.configuration import Config
import joblib
import os.path as path


CFG = Config()
trainer_store = joblib.load(path.join(CFG.base_path, CFG.model_files_path, CFG.text_category_model))


def predict_text_category(text):
    category = trainer_store.model.predict([text])[0]
    print(category)
    return category