from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from superpilot.examples.persona.query_process import query_process_agent

app = FastAPI()

# Define ground_truth
ground_truth = """
World War II (1939-1945) was the most devastating and widespread conflict in human history, involving more than 100 million people from over 30 countries. It began with Germany's invasion of Poland on September 1, 1939, prompting Britain and France to declare war on Germany. The war was primarily fought between the Axis Powers—Germany, Italy, and Japan—and the Allies, including Britain, France, the Soviet Union, China, and the United States.

**Historical Context:** The roots of World War II can be traced back to the aftermath of World War I and the Treaty of Versailles (1919), which imposed harsh penalties on Germany. Economic instability, nationalism, and resentment fueled the rise of Adolf Hitler and the Nazi Party in Germany, which sought to restore German power and expand its territory. In the Pacific, Japan pursued imperial expansion, invading China in 1937. Italy, under Benito Mussolini, also sought to build a new Roman Empire, leading to invasions in Africa and Europe.

**Geopolitical Impact:** The war dramatically reshaped global geopolitics. The defeat of Nazi Germany, Imperial Japan, and Fascist Italy ended the Axis threat, but it also gave rise to the Cold War. The United States and the Soviet Union emerged as the two dominant superpowers, with conflicting ideologies—capitalism and communism—driving decades of tension. Europe's influence declined as many of its colonies in Africa, Asia, and the Middle East sought independence, leading to the decolonization movement. Germany was divided into East and West, and Japan was occupied by U.S. forces until 1952.

**Economic Effects:** The economic toll of World War II was staggering. Europe and Asia were left in ruins, with industries destroyed and millions displaced. The U.S. economy, however, emerged stronger, having ramped up production for the war effort and avoided destruction on its soil. The Marshall Plan, launched by the U.S. in 1948, helped rebuild Europe and restore economic stability. In contrast, the Soviet Union expanded its control over Eastern Europe, imposing communist regimes, which led to the creation of the Eastern Bloc.

**World Trade and Globalization:** The war disrupted global trade, but it also laid the groundwork for modern international trade systems. Institutions like the United Nations, World Bank, and International Monetary Fund were created to promote peace, economic cooperation, and stability. The war also spurred technological advancements, such as radar, jet engines, and nuclear energy, which would shape global industries in the post-war era.

Overall, World War II reshaped political alliances, economies, and international relations, setting the stage for the modern world.
"""

# Define input model for the API
class QueryRequest(BaseModel):
    query: str


# Define the POST API route
@app.post("/process_query/")
async def process_query(request: QueryRequest):
    try:
        response = await query_process_agent(query=request.query, ground_truth=ground_truth)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from superpilot.examples.persona.query_process import query_process_agent

app = FastAPI()

# Define ground_truth


# Define input model for the API


class QueryRequest(BaseModel):
    query: str


# Define the POST API route
@app.post("/process_query/")
async def process_query(request: QueryRequest):
    try:
        response = await query_process_agent(query=request.query, ground_truth=ground_truth)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""