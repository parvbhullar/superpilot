import sys
import os
import asyncio

# Add the parent directory to the system path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

#Doc api evaluation

from superpilot.core.evals.doc_eval import doc_eval_value


# Add the parent directory to the system path for imports
#openai_api_key=os.getenv('OPENAI_API_KEY')


questions=['Global digital remittance market growth','Key players in digital remittance?','What drives digital remittance growth?','Cultural tourism growth in India','Impact of movies on travel','Heritage tourism market booking channels','Electronic warfare market growth forecast','Key players in electronic warfare','Driving factors of electronic warfare']

truth1="""
The sheer magnitude of the global migrant labor force, coupled with the frequency and magnitude of their financial transactions, positions them as a dominant and influential user category, cementing their role as a primary driving factor within the digital remittance market.
Recent Developments
In 2022, Western Union made a significant move by acquiring Uphold, a digital currency exchange. This strategic acquisition positions Western Union to broaden its array of remittance choices, notably introducing cryptocurrency options for its customer base.
In 2022, PayPal strengthened its digital remittance services by acquiring Curv, a digital asset security firm. This acquisition bolsters PayPal's security capabilities, enhancing the safety of its digital remittance offerings.
In 2022, acquired TransferWise, a fellow digital remittance company. This merger forms a more expansive and diverse digital remittance provider, catering to a broader spectrum of user needs.
In 2021, Ant Group, the parent company of Alipay, joined forces with Western Union, forging a partnership aimed at facilitating cross-border remittances in China. This collaboration simplifies and economizes the process of sending money overseas for Chinese consumers.
In 2021, Mastercard collaborated with Remitly, a digital remittance company. This partnership equips Mastercard cardholders with a streamlined avenue for sending funds to Mexico, ensuring greater ease and convenience in supporting their loved ones south of the border.
In August 2021, WorldRemit Ltd. launched its money transfer services in Malaysia, allowing WorldRemit users to send money from Malaysia, in addition to 50 other countries, including the U.S. and the U.K., to more than 130 destinations.
Digital Remittance Market Players
Azimo Limited
Digital Wallet Corporation
InstaReM Pvt. Ltd.
MoneyGram
PayPal Holdings, Inc.
Ria Financial Services Ltd.
TransferGo Ltd.
TransferWise Ltd.
Western Union Holdings, Inc.
WorldRemit Ltd.
Segments Covered in the Report
By Type
Inward Digital Remittance
Outward Digital Remittance
By Channel
Banks
Money Transfer Operators
Online Platforms
Others
By End-use
Migrant Labor Workforce
Personal
Small Businesses
Others
By Geography
North America
Europe
Asia-Pacific
Latin America
Middle East and Africa
Frequently Asked Questions
What is the digital remittance market size?                                      
The global digital remittance market size is expected to increase USD 77.6 billion by 2032 from USD 19.1 billion in 2022.                                      
What will be the CAGR of global digital remittance market?
"""

truth2="""
As audiences become captivated by the storytelling and visual portrayal of historical events, they desire to visit the featured sites, which can lead to increased heritage tourism. Furthermore, these entertainment mediums provide an engaging look into the past, arousing curiosity and interest in historical eras and iconic locations showcased in the narratives.
An article published in Business Standard on October 2023 says that almost 94% of Indians are inspired by movies or TV shows for travel destinations that they've seen on the big or small screen, be it Paris, inspired by the hit sitcom ‘Emily in Paris, or Manali, shown in superhit film ‘Yeh Jawaani Hai Deewani.
Type insights
The cultural segment dominated the global heritage tourism market in 2023. This growth is due to the abundance of cultural sites and the strong preference among travelers for visiting historical and cultural locations. Cultural sites, encompassing monuments, buildings, and artifacts, possess a tangible presence. Also, these sites are regarded as valuable for preservation and are highly popular among cultural tourists. This trend is anticipated to contribute positively to the expansion of the cultural tourism market.
In June 2023, Airbnb signed a memorandum of understanding with India’s Ministry of Tourism to showcase the country’s heritage stays and promote cultural tourism. As part of the ministry’s ‘Visit India 2023’ initiative, Airbnb will launch a dedicated ‘Soul of India’ microsite and offer support to hosts in untapped tourist areas to assist them in promoting their homestays and building host capacity for fostering a culture of responsible hosting.
The natural segment is expected to grow at a faster pace in the heritage tourism market over the forecast period. Natural heritage, including national parks, wildlife sanctuaries, and picturesque landscapes, attracts travelers eager to experience nature's beauty and tranquility. The appeal of untouched environments and eco-tourism opportunities draws nature lovers and adventure enthusiasts to these locations. Sustainable tourism visits to UNESCO natural heritage sites are on the rise, and this aims to minimize the impact of human activity on these areas.
Booking Channel Insights
The offline segment led the heritage tourism market in 2023. This demographic tends to book trips through travel agents and other offline channels because of the convenience and simplicity of the services offered. This is due to the greater consumer preference and perception of offline channels. Additionally, these channels' longstanding nature and widespread availability worldwide are anticipated to influence the global market significantly. Thus, baby boomers and the older generation are significant travelers in the global market.
"""

truth3="""
frequently_asked_questions:[{'question': 'What is the electronic warfare market size?', 'answer': 'The global electronic warfare market size was exhibited at USD 22.4 billion in 2022, and is expected to hit around USD 36.56 billion by 2032.'}, {'question': 'What will be the CAGR of global electronic warfare market?', 'answer': 'The global electronic warfare market will register growth rate of 5.02% between 2023 and 2032.'}, {'question': 'Who are the prominent players operating in the electronic warfare market?', 'answer': 'The major players operating in the electronic warfare market are BAE Systems plc,, Elbit Systems Ltd., General Dynamics Corporation, Israel Aerospace Industries Ltd. (IAI), L3Harris Technologies Inc., Leonardo SpA, Lockheed Martin Corporation, Northrop Grumman Corporation, Raytheon Technologies Corporation, SAAB AB, Thales Group, and Others.'}, {'question': 'Which are the driving factors of the electronic warfare market?', 'answer': 'The driving factors of the electronic warfare market are the rising advancements in technology, evolving threats in the electronic domain, and the need for modern military forces to maintain a competitive edge.'}, {'question': 'Which region will lead the global electronic warfare market?', 'answer': 'North America region will lead the global electronic warfare market during the forecast period 2023 to 2032.'}]
main_content:The global electronic warfare market size was valued at USD 22.4 billion in 2022, and it is anticipated to surpass around USD 36.56 billion by 2032, expanding at a CAGR of 5.02% during the forecast period 2023 to 2032.
To Access our Exclusive Data Intelligence Tool with 15000+ Database, Visit: Precedence Statistics 
Key Takeaways:
North America contributed more than 46% of market share in 2022.
Asia-Pacific region is expected to expand at the fastest CAGR between 2023 and 2032.
By Domain, the electronic support segment captured the largest revenue share in 2022.

"""

result=[]
ground_truth=[truth1,truth1,truth1,truth2,truth2,truth2,truth3,truth3,truth3]


"""
def get_response(query):
    
    # Define the URL and the payload
    url = "http://qa-search-service.co/api/v1/search/query/docs/?page=1&page_size=1"
    payload = {
        "query": query,
        "kn_token": []
    }

    # Measure the time taken for the request
    start_time = time.time()
    response = requests.post(url, json=payload,timeout=5)
    end_time = time.time()

    # Calculate the response time
    response_time = end_time - start_time

    # Print the response status code, time taken, and the response data
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Time: {response_time:.4f} seconds")
    result=response.json()
    main_content=str(result["data"][0]["content"])

    #print (main_content)
    print()
    return main_content,response_time


for i in range(9):
    answer,times=get_response(questions[i])
    data_samples={
                'question':[questions[i]],
                'answer':[answer],
                'ground_truth':[ground_truth[i]],
            }
    dataset = Dataset.from_dict(data_samples)
    start_time = time.time()
    score = evaluate(dataset,metrics=[answer_correctness])
    end_time=time.time()
    response_time=end_time-start_time
    #eval_time.append(response_time)
    sc=score.to_pandas()
    sc['api_time']=times
    sc['eval_time']=response_time
    result.append(sc)

    print(sc['answer_correctness'])


final_result = pd.concat(result, ignore_index=True)
final_result.to_csv('docs_eval.csv',index=False)

"""


for i in range(9):
    sc=doc_eval_value(questions[i],ground_truth[i])
    result.append(sc)

print(result)

    