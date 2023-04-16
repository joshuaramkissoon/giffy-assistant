from langchain import SerpAPIWrapper, LLMChain
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.utilities import WikipediaAPIWrapper
import logging

PROMPT_PREFIX = """Have a conversation with a human, answering the following questions as best you can. You have access to the following tools:"""
PROMPT_SUFFIX = """Begin!"

{chat_history}
Question: {input}
{agent_scratchpad}"""

class Agent:
    
    def __init__(self):
        search = SerpAPIWrapper()
        wikipedia = WikipediaAPIWrapper()
        tools = [
            Tool(
                name="Intermediate Answer",
                func=search.run,
                description="useful for when you need to ask with search"
            ),
            Tool(
                name="Wiki",
                func=wikipedia.run,
                description="Search for information on wikipedia"
            ),
        ]
        
        prompt = ZeroShotAgent.create_prompt(
            tools, 
            prefix=PROMPT_PREFIX, 
            suffix=PROMPT_SUFFIX, 
            input_variables=["input", "chat_history", "agent_scratchpad"]
        )
        memory = ConversationBufferMemory(memory_key="chat_history")
        
        llm_chain = LLMChain(llm=OpenAI(temperature=0), prompt=prompt)
        agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True)
        self.agent = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory)
        

    def ask(self, input: str):
        response = None
        try:
            response = self.agent.run(input=input)
        except ValueError:
            try:
                logging.warn("Retrying agent request, ValueError raised")
                response = self.agent.run(input=input)
            except ValueError as e:
                logging.error(f"AgentError: {e}")
        logging.info(f"Agent generated response={response}")
        return response
        