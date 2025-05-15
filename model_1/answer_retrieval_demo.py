import json
import time
import random
import os
import chromadb
import autogen
from autogen import ConversableAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from typing import Annotated

########################## SETTING UP API ##########################
config_list = [
    {
        "model": "gpt-4o-mini",
        "api_key": os.environ["OPENAI_API_KEY"]
    }
]
########################## CUSTOM JSON TEXT SPLITTER ##########################
def jsonl_text_splitter(file_content, chunk_token_size=2000):
    chunks = []
    try:
        data = json.loads(file_content)  # parse full JSON array
        for item in data:
            #time.sleep(1)
            #print("Item: ", item)
            
            q = item.get("Question", "").strip()
            a = item.get("Response", "").strip()
            if q or a:
                formatted = f"Question: {q}\nResponse: {a}"
                #print(formatted)
                chunks.append(formatted)
    except json.JSONDecodeError:
        print("Failed to parse JSON array.")
    print("chunks created successfully. i hope")
    return chunks

def rag_iterator(num):
    nums = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
    for num in nums:
        yield num
    return "out of databases"

it = rag_iterator(10)

########################## RAG TOOL ##########################
def rag_chat(message: Annotated[str, "The question that you need answered"], n_results: Annotated[int, "number of results"] = 1):


    num = next(it)
    if num == "out of databases":
        return num
    
    print(f"./hospital_data/{num}")
    
    # RAG Agents
    # Task: Return data from a database
    # Method: chroma
    # Notes: Has custom text splitting function
    #        Makes a database once, then reuses it
    #        Ten agents total
    hospital_agent_1 = RetrieveUserProxyAgent(
        name = "hopsital_agent_1",
        default_auto_reply="Reply `TERMINATE` if the task is done.",
        retrieve_config={
            "task": "qa",
            "docs_path": f"./hospital_data/{num}",
            "model": config_list[0]["model"],
            "client": chromadb.PersistentClient(path=f"./chromadb/{num}"),
            "get_or_create": True,
            #"overwrite": True,
            "context_max_token": 21000,
            "chunk_token_size": 2000,
            "collection_name": num,
            "chunk_mode": "one_line",
            "custom_text_split_function": jsonl_text_splitter,
            "customized_prompt": """Context: {input_context}""" 
        


        },
        human_input_mode="NEVER",
        code_execution_config=False,
        max_consecutive_auto_reply=3 # Not needed, only gives one message

    )

    hospital_agent_1.n_results=n_results
    context = {"problem": message, "n_results": n_results}

    # This one line is responsible for running the RAG search
    response = hospital_agent_1.message_generator(hospital_agent_1, None, context )

    # print("Response by the RAG Agent:\n\n", response, "\n\nResponse ended")
    return response




def main():
    


    
    
    ########################## DEFINE SYSTEM MESSAGES ##########################
    # Answer Finder System Message
    # TLDR: The agent should call the RAG function "rag_chat" 
    #       to find the answer to a question.
    #       If the Q/A pair does not match, call the function again.
    answer_finder_system_message = """You are an assistant who will be asked a question by a user. 
    You do not have the answer to this question. your job is to find this answer. 
    You have a function that might be able to generate the answer for you.
    You should give the user's prompt, verbatum, as a parameter to the function.
    Then, the function will attempt to return a question/answer pair. The answer will be labeled as "response".
    If (AND ONLY IF) the function returns the EXACT same question that the user asked, should you accept that answer.
    This does not just mean same topic - it means EXACT same question. You will find the returned data under the "Context" field.

    Example question: "Question": "What is the most likely direct cause of the 11-year-old boy's symptoms of vomiting, morning worsening of symptoms, occasional headaches, and mild narrowing of visual fields, considering his intact cranial nerves and visual symptoms?

    Example WRONG response: "Question": What is the most likely cause of a 14-year-old boy's symptoms of vomiting, worse symptoms in the morning, frequent headaches, and extreme narrowing of visual field?
    you would NOT accept such a question/response pair as correct, as it does not quite match the user's question

    Example CORRECT response: "Question": "What is the most likely direct cause of the 11-year-old boy's symptoms of vomiting, morning worsening of symptoms, occasional headaches, and mild narrowing of visual fields, considering his intact cranial nerves and visual symptoms?
    this matches the string EXACTLY, and the response should be returned. 

    You should only consider what is returned from the function under the "Context is:" part. everything above that is irrelevant.
    Once you are given a question/answer pair as described above, you should repeat the answer so that the user can have it.
    If you did not get a question that matches your question, you should call the function again, and it will return new information.
    Repeat this process until you get the correct question/answer pair, OR the function returns "out of databases" in the case of the latter, your answer should be "unable to find".
    Upon giving an answer to a user, you should end your message with "TERMINATE"
    """
    # Verifier System Message
    # Return True or False based on whether an answer is correct
    verifier_system_message = """You are a verifier who checks if the answer to a question is correct. Respond with 'true' or 'false' only. Here is the answer:\n"""
    
    ########################## SETTING UP ENVIRONMENT ##########################
    start_time = time.time()
    with open('medical_o1_sft.json', 'r') as file:
        data = json.load(file)
    

    
    
    # Creating question/answer pair
    question_CoT_Answer_Group = random.choice(data[0:25370])
    question = question_CoT_Answer_Group.get('Question', 'Question not found')
    answer = question_CoT_Answer_Group.get('Response', 'Response not found')

    # Output q/a pair
    print("\nQuestion\n",question)
    print("\nAnswer\n",answer)

    # Giving the verifier the answer
    verifier_system_message += answer
 

    ########################## DEFINE AGENTS ##########################

    # Answer Finder Agent
    # Task: Call upon RAG to search for the answer to a question
    # Termination: Upon verifier (user for now) confirming answer is true 
    #              or encountering an error
    # Capabilities: Can give parameters to function rag_chat()
    # Model: GPT-4o-mini
    answer_finder_agent = ConversableAgent(
        "answer_finder_agent", 
        system_message=answer_finder_system_message, 
        llm_config=config_list[0],
        human_input_mode="NEVER",
        is_termination_msg=lambda msg: msg.get("content") and "TERMINATE" in msg.get("content")
    )

    # Verifier Agent
    # Not yet implemented into workflow
    # Task: Compare two answers, one is in its system message, 
    #       the other is in the user message (given by answer_finder_agent)
    # Termination: N/A
    # Model: GPT-4o-mini
    verifier = ConversableAgent(
        name="Verifier",
        llm_config=config_list[0],
        system_message=verifier_system_message,
        human_input_mode="NEVER"
    )
    
    # User Proxy Agent
    # Task: Stand-in for the user, hold a direct chat with answer_finder_agent
    #       Execute functions
    # Human Interference: Currently none
    # Model: None (No LLM)
    user_proxy_agent = autogen.UserProxyAgent(
        name = "user_proxy",
        human_input_mode="NEVER",
        is_termination_msg=lambda msg: msg.get("content") and "TERMINATE" in msg.get("content"),
        code_execution_config=False

    )

    ########################## SETTING UP TOOLS ##########################
    # Two-Step Method
    # Tools can only be executed by two agents in a chat

    # Give answer_finder_agent the ability to suggest parameters
    answer_finder_agent.register_for_llm(
        name="rag_chat",
        description="This is the function that will search for an answer"
        )(rag_chat)
    # Give user_proxy_agent the ability to actually execute the function
    user_proxy_agent.register_for_execution(name="rag_chat")(rag_chat)



    

    ########################## CHAT ##########################
    chat_history = user_proxy_agent.initiate_chat(answer_finder_agent,
        message=question
    )


    ########################## SUMMARY ##########################
    print("LLM's Answer:\n", chat_history.summary)
    print("Ground Truth Answer:\n", answer)

    end_time = time.time()
    print(f"Total Time: {end_time - start_time:.2f} seconds")



if __name__ == "__main__":
    main()