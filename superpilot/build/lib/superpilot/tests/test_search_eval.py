import sys
import os
import asyncio

# Add the parent directory to the system path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


from superpilot.core.memory.vespa_memory import MemoryManager
from datasets import Dataset 
from ragas.metrics import answer_relevancy,faithfulness, answer_correctness
from ragas import evaluate
import re
import pandas as pd

from transformers import pipeline
#vespa_url='https://fb73ae7d.baed2213.z.vespa-app.cloud/'
vespa_url='http://localhost:8081/'
memory=MemoryManager(store_url=vespa_url,ref_id='test_memory')




#---------------------------------------------------------------------
#Eval of Queries



# Load the summarization pipeline from transformers
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def get_main_content(questions):
    main_contents = []
    for question in questions:
        # Summarize the question
        summary = summarizer(question, max_length=10, min_length=5, do_sample=False)
        main_contents.append(summary[0]['summary_text'])
    return main_contents

def get_main_keyword_content(questions):
    main_keywords = []
    for question in questions:
        # Normalize the question and remove any punctuation
        question = question.lower().strip()
        
        # Define a pattern to extract keywords related to AI and healthcare
        # This regex captures phrases like 'AI in healthcare'
        pattern = r'\b(ai in healthcare|predictive analytics|decision support systems|personalized treatment plans|challenges in healthcare)\b'
        
        # Search for the pattern in the question
        match = re.search(pattern, question)
        if match:
            main_keywords.append(match.group(0))  # Get the matched keyword
        else:
            main_keywords.append("No main keyword found")  # Fallback if no match
        
    return main_keywords

def get_main_query(questions):
    # Use an NLP model to extract important words (e.g., using distilBERT, GPT models, etc.)
    summarizer = pipeline("summarization")
    main_queries = []

    for question in questions:
        # Shorten the question into a 5-word summary using an NLP model
        summary = summarizer(question, max_length=5, min_length=5, do_sample=False)
        main_query = summary[0]['summary_text']
        # Clean up and remove extra spaces
        main_query = re.sub(r'\s+', ' ', main_query).strip()
        main_queries.append(main_query)
    
    return main_queries


questions=[
    
    'How is Artificial Intelligence (AI) transforming patient care in healthcare?',
    'How is Artificial Intelligence (AI) reshaping patient care through predictive analytics and decision support systems?',
    'What challenges arise from the use of AI in healthcare, and how can they be addressed?',
    'How do AI-driven predictive analytics contribute to disease prevention and early diagnosis?',
    'How are AI algorithms improving diagnostic accuracy and efficiency in medical imaging?']

answers=[
    'AI is revolutionizing patient care through predictive analytics, decision support systems, and personalized treatment plans. Predictive analytics help in early disease prevention by identifying patterns and risk factors, improving diagnosis and outcomes. Machine learning tailors interventions to individual patients, while AI-driven medical imaging enhances diagnostic accuracy. AI-powered decision support systems streamline workflows by providing real-time insights and evidence-based recommendations. Remote patient monitoring, facilitated by AI, enables proactive healthcare by tracking vital signs and identifying potential health issues in real-time, ultimately improving patient care and reducing costs.',
    
    'AI is transforming patient care by using predictive analytics and decision support systems to analyze structured and unstructured healthcare data, such as electronic medical records and medical images. Techniques like machine learning and deep learning help identify patterns and trends in patient data that may not be obvious to humans. This enables earlier diagnosis, more effective treatments, and better prognosis evaluations. AI-driven tools enhance decision-making and streamline healthcare processes, ultimately improving outcomes and patient care delivery.',

    'While AI optimizes hospital operations and enhances resource allocation, challenges such as data privacy, algorithmic biases, and the potential replacement of human judgment must be addressed. Ensuring safe and ethical use of AI in healthcare involves implementing robust data privacy regulations, developing transparent algorithms to minimize biases, and maintaining human oversight in critical decision-making processes. These steps are crucial to building trust and ensuring that AI serves as a complement to, rather than a replacement for, human expertise in healthcare.',

    'AI-driven predictive analytics contribute to disease prevention and early diagnosis by analyzing large datasets to identify patterns and risk factors. These insights enable healthcare professionals to predict the likelihood of diseases such as diabetes, cardiovascular conditions, and certain cancers. Early detection improves treatment outcomes and reduces healthcare costs by preventing the need for more extensive and expensive interventions. AIs ability to analyze complex data efficiently makes it a valuable tool for proactive disease management and improved patient care.',

    'AI algorithms enhance diagnostic accuracy and efficiency in medical imaging by analyzing images such as X-rays, MRIs, and CT scans. Machine learning models, trained on large datasets, can detect anomalies quickly and accurately, providing faster diagnoses. This accelerates the diagnostic process and aids healthcare professionals in making more informed decisions about patient care. AIs precision in medical imaging reduces human error and improves overall healthcare outcomes by ensuring timely and accurate assessments'
    ]

keyword=get_main_query(questions)
#keyword.pop()
#keyword.append('AI integration face in healthcare')
#print(keyword)
keywords=['Artificial Intelligence (AI) transforming patient care in healthcare','Artificial Intelligence (AI) reshaping patient care','AI in healthcare','AI-driven predictive analytics contribute to disease prevention and early diagnosis','AI algorithms improving diagnostic accuracy and efficiency in medical imaging']
contexts=[]
filter_dict={}
for query in keywords:
    answer=[]
    top_chunks=memory.search(query,filter_dict)

    for chunks in top_chunks:
        if len(str(chunks.content).split())>100:
                answer.append(chunks.content)
        
    print("Response of Query",len(answer))

    contexts.append(answer)

#Answer relevance
# data_samples={
#     'question':questions,
#     'answer':answers,
#     'contexts':contexts,
    
# }

# #print(data_samples)
# result=[]
# for i in range(5):
#     for context in contexts[i]:
#         data_samples={
#             'question':[questions[i]],
#             'contexts':[context],
#             'answer':[answers[i]],
#         }
#         dataset = Dataset.from_dict(data_samples)
#         score = evaluate(dataset,metrics=[answer_relevancy])
#         sc=score.to_pandas()
#         sc['metrics'] = 'answer relevancy'
#         print(f'Result{i}',sc)
#         result.append(sc)


# result['metrics'] = 'answer correctness'

# csv_file_path = 'evaluation_results.csv'  # Specify your desired file path
# result.to_csv(csv_file_path, index=False)
    



# dataset = Dataset.from_dict(data_samples)
# #print(dataset.to_dict())
# score = evaluate(dataset,metrics=[answer_relevancy])
# result=score.to_pandas()


# print("Result",result)
# result['metrics'] = 'answer relevance'

# csv_file_path = 'evaluation_results.csv'  # Specify your desired file path
# result.to_csv(csv_file_path, index=False)
# print(f"Results have been saved to {csv_file_path}")

#-----------------------------------------
#Answer Correctness
print('Context Length',len(contexts))
result=[]
for i in range(5):
    for context in contexts[i]:
        data_samples={
            'question':[questions[i]],
            'answer':[context],
            'ground_truth':[answers[i]],
        }
        dataset = Dataset.from_dict(data_samples)
        score = evaluate(dataset,metrics=[answer_correctness])
        sc=score.to_pandas()
        sc['metrics']='correctness'
        #print(f'Result{i}',sc)
        result.append(sc)
print("Final Result")
print(result)

final_result = pd.concat(result, ignore_index=True)

# Save the DataFrame to a CSV file
final_result.to_csv('evaluation_results.csv', index=False)

print("Final Result saved in 'evaluation_results.csv'")


# result['metrics'] = 'answer correctness'

# csv_file_path = 'evaluation_results.csv'  # Specify your desired file path
# result.to_csv(csv_file_path, index=False)



# # Assuming evaluate and answer_correctness are defined elsewhere





# def evaluate_sample(args):
#     """Evaluate samples for a single question and its contexts."""
#     i, question, contexts, ground_truth = args
#     results = []

#     for context in contexts:
#         data_samples = {
#             'question': [question],
#             'answer': [context],
#             'ground_truth': [ground_truth],
#         }
        
#         dataset = Dataset.from_dict(data_samples)
#         score = evaluate(dataset, metrics=[answer_correctness])
#         sc = score.to_pandas()
#         sc['metrics'] = 'answer correctness'  # Add metrics column
#         results.append(sc)

#     return pd.concat(results, ignore_index=True) if results else pd.DataFrame()

# # Prepare arguments for the Pool
# args = [(i, questions[i], contexts[i], answers[i]) for i in range(5)]

# # Initialize a list to collect results
# results = []

# # Use a Pool for parallel processing
# with Pool() as pool:
#     results = pool.map(evaluate_sample, args)

# # Concatenate all results into a single DataFrame
# final_result = pd.concat(results, ignore_index=True)

# # Save the results to a CSV file
# final_result.to_csv('correctness_results.csv', index=False)

# print("Results saved to correctness_results.csv")
