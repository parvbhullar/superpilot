import sys
import os
import asyncio

# Add the parent directory to the system path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


from superpilot.core.memory.vespa_memory import MemoryManager

from datasets import Dataset 
from ragas.metrics import answer_relevancy,faithfulness, answer_correctness
from ragas import evaluate

#Doc api evaluation


# Add the parent directory to the system path for imports
openai_api_key=os.getenv('OPENAI_API_KEY')


#Agents Eval:

import pandas as pd

question=['Most important inventions of the 21st century','Most important inventions of the 21st century']
radio="The Radio Archivist is dedicated to collecting and preserving vintage radio broadcasts, with a particular focus on the transformative years of radio from the 1920s to the 1940s. It explores the development of recording technologies that revolutionized the way radio shows were produced and disseminated. This persona delves into the lives and careers of notable radio personalities, highlighting their contributions to entertainment and culture. Key programs such as 'Amos 'n' Andy' and 'The Jack Benny Program' are explored for their impact on audiences and the evolution of comedic storytelling in audio format. By bringing together rare recordings and historical context, the Radio Archivist serves as a vital resource for radio enthusiasts and historians alike."
historian="Technology Historian will provide a detailed analysis of significant inventions, such as smartphones, artificial intelligence, and renewable energy technologies. She will contextualize these innovations within societal changes, discussing their impact on communication, productivity, and environmental sustainability. Drawing from her academic research, she will highlight how these inventions have revolutionized industries and influenced daily life. By presenting case studies and historical data, Dr. Carter aims to educate readers on the transformative power of these inventions and provoke thought about future innovations."
entrepreneur="Tech Entrepreneur will share insights from his entrepreneurial journey, emphasizing inventions that have reshaped industries. He will discuss how technologies like the Internet of Things (IoT) and machine learning have revolutionized business operations and consumer experiences. By providing real-world examples of how these inventions have been implemented in his companies, Alex will inspire aspiring entrepreneurs and highlight the importance of innovation in today's economy."
scientist='Environmental Scientist will focus on inventions that contribute to sustainability and environmental preservation, such as solar energy technologies, electric vehicles, and biodegradable materials. She will explain how these innovations address pressing global challenges and promote a greener future. Her perspective will emphasize the importance of these inventions not just for technology but for the health of the planet, making a compelling case for their significance in the 21st century.'
analyst="Policy Analyst will provide a critical analysis of the most important inventions of the 21st century from a policy perspective. She will discuss how innovations like artificial intelligence, big data, and biotechnology influence regulations and societal norms. Her insights will highlight the challenges and opportunities posed by these inventions, advocating for policies that promote responsible innovation. By analyzing current trends and potential future developments, Sarah aims to guide policymakers in making informed decisions that shape the technological landscape."



answer=['Radio Archivist',radio]
ground_truths=[['Technology Historian',historian],['Tech Entrepreneur ',entrepreneur],['Environmental Scientist',scientist],['Policy Analyst',analyst]]

result=[]
for truth in ground_truths:
    data_samples={
                'question':question,
                'answer':answer,
                'ground_truth':truth,
            }
    dataset = Dataset.from_dict(data_samples)
    score = evaluate(dataset,metrics=[answer_correctness])
    sc=score.to_pandas()
    sc['metrics']='correctness'
    result.append(sc)
    print(truth[0])
    print(sc['answer_correctness'])


final_result = pd.concat(result, ignore_index=True)

# Save the DataFrame to a CSV file
final_result.to_csv('agents_eval.csv', index=False)

print("Final Result saved in 'agents_eval.csv'")


result=[]
for truth in ground_truths:
    print(truth)
    data_samples={
                'question':question,
                'answer':answer,
                'contexts':[truth,truth],
            }
    dataset = Dataset.from_dict(data_samples)
    score = evaluate(dataset,metrics=[answer_relevancy])
    sc=score.to_pandas()
    sc['metrics']='answer_relevancy'
    result.append(sc)
    print(truth[0])
    print(sc['answer_relevancy'])


final_result = pd.concat(result, ignore_index=True)

final_result.to_csv('agents_eval.csv', mode='a', header=False, index=False)
