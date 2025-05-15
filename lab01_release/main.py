from typing import Dict, List
from autogen import ConversableAgent
import sys
import os
from math import sqrt

def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    # TODO
    # This function takes in a restaurant name and returns the reviews for that restaurant. 
    # The output should be a dictionary with the key being the restaurant name and the value being a list of reviews for that restaurant.
    # The "data fetch agent" should have access to this function signature, and it should be able to suggest this as a function call. 
    # Example:
    # > fetch_restaurant_data("Applebee's")
    # {"Applebee's": ["The food at Applebee's was average, with nothing particularly standing out.", ...]}
    result = {}
    
    with open("restaurant-data.txt", 'r') as file:
        lines = file.readlines()
        
        for line in lines:
            line = line.strip()
            if line.startswith(restaurant_name):
                if restaurant_name not in result:
                    result[restaurant_name] = []
                result[restaurant_name].append(line)
    
    
    if not result:
        return {"Error": ["Restaurant name incorrect. List of valid names: McDonald's, Subway, Taco Bell, Chick-fil-A, Applebee's, Olive Garden, Cheesecake Factory, "
                "Buffalo Wild Wings, Starbucks, Krispy Kreme, Panera Bread, Tim Horton's, Chipotle, In-n-Out, Five Guys, Panda Express, Pret A Manger, Cinnabon, IHOP, Burger King"]}
    print(f"Length of result: {len(result[restaurant_name])}")
    return result
    return {"McDonald's": ["The food at McDonald's was average, with nothing particularly standing out."]}
    pass


def calculate_overall_score(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> Dict[str, float]:
    # TODO
    # This function takes in a restaurant name, a list of food scores from 1-5, and a list of customer service scores from 1-5
    # The output should be a score between 0 and 10, which is computed as the following:
    # SUM(sqrt(food_scores[i]**2 * customer_service_scores[i]) * 1/(N * sqrt(125)) * 10
    # The above formula is a geometric mean of the scores, which penalizes food quality more than customer service. 
    # Example:
    # > calculate_overall_score("Applebee's", [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    # {"Applebee's": 5.048}
    # NOTE: be sure to that the score includes AT LEAST 3  decimal places. The public tests will only read scores that have 
    # at least 3 decimal places.

    n = len(food_scores)
    return sum(
        sqrt(food_scores[i]**2 * customer_service_scores[i]) * (1 / (n * sqrt(125))) * 10
        for i in range(n)
    )
    print("TOTAL SCORE: ", total_score)
    exit()

    return 6.000
    pass

def get_data_fetch_agent_prompt(restaurant_query: str) -> str:
    # TODO
    # It may help to organize messages/prompts within a function which returns a string. 
    # For example, you could use this function to return a prompt for the data fetch agent 
    # to use to fetch reviews for a specific restaurant.
    pass

# TODO: feel free to write as many additional functions as you'd like.

# Do not modify the signature of the "main" function.
def main(user_query: str):
    
    entrypoint_agent_system_message = "You are a helpful AI Assistant. You will be receiving prompts from other AI agents. Please work well with them." # TODO
    # example LLM config for the entrypoint agent
    llm_config = {"config_list": [{"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]}]}
    # the main entrypoint/supervisor agent
    
    
    
    entrypoint_agent = ConversableAgent(
        "entrypoint_agent", 
        system_message=entrypoint_agent_system_message, 
        llm_config=llm_config,
        human_input_mode="NEVER",
        is_termination_msg=lambda msg: msg.get("content") and "TERMINATE" in msg.get("content"),
    )
    entrypoint_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)
    entrypoint_agent.register_for_execution(name="calculate_overall_score")(calculate_overall_score)
    
    # TODO
    # Create more agents here. 
    data_fetch_agent = ConversableAgent(
        "data_fetch_agent", 
        system_message="""Your job is to fetch data about a restaurant's reviews. 
        When calling a function, please capitalize and punctuate the restaurant's names correctly. 
        This includes hyphens and apostrophe's where needed. They may be incorrect in the prompt.
        Once you receive the function's output, you need to state it in its entirety.
        Please try to output all reviews, there should be roughly 40. You must output all 40 lines, each review is necessary for future processing.
        Please do not attempt to summarize the output or leave any reviews out.
        Then, end your message with TERMINATE.
        """,
        llm_config=llm_config
        )
    data_fetch_agent.register_for_llm(name="fetch_restaurant_data", description="Fetches the reviews for a specific restaurant.")(fetch_restaurant_data)
    print("data_fetch_agent setup successful")

    review_agent = ConversableAgent(
        "review_analysis_agent",
        system_message="""
            You are a helpful AI assistant whose job is to transform a list of reviews into numerical ratings. 
            This is the basic schema: you have a list of adjectives that each correspond to a number. Each review has two components: a comment about the food quality, 
            and a comment about the customer service quality. You must discern between the two and assign two numbers for each review. 
            Here are the adjectives and their point values: Score 1/5 has one of these adjectives: awful, horrible, or disgusting.
            Score 2/5 has one of these adjectives: bad, unpleasant, or offensive.
            Score 3/5 has one of these adjectives: average, uninspiring, or forgettable.
            Score 4/5 has one of these adjectives: good, enjoyable, or satisfying.
            Score 5/5 has one of these adjectives: awesome, incredible, or amazing. Your score should be entirely based upon these adjectives.
            Here is what your output should look like: 
            <restaurant_name>:
            1. Food: <food_rating>, Customer Service: <customer_service_rating>
            2. Food: <food_rating>, Customer Service: <customer_service_rating>
            Keep going until all reviews have been converted.
            If you do not receive all 40 reviews from the prompt, you should assume that a pattern is followed.
            You must return numerical ratings for all 40 reviews.
            Oh, and if you think that customer service or food quality is not mentioned give the missing field a value of 3, and put an asterisk next to it.
            You don't need to put an asterisk next to its counterpart. This will be so that the user can debug.
            End your message with TERMINATE.
            """,
        llm_config=llm_config
    )

    scoring_agent = ConversableAgent(
        "scoring_agent",
        system_message="""
        You are a helpful AI assistant who will need to take a list of numbers and pass them into a function. 
        The first column will be one list, the second column will be another.
        Please round the function output to 3 decimal places. No additional content is needed, you should only return the number.
        """,
        llm_config=llm_config
    )

    scoring_agent.register_for_llm(name="calculate_overall_score", description="Will take the average of every review of food and customer service.")(calculate_overall_score)
    # TODO
    # Fill in the argument to `initiate_chats` below, calling the correct agents sequentially.
    # If you decide to use another conversation pattern, feel free to disregard this code.
    
    # Uncomment once you initiate the chat with at least one agent.
 
    """
    entrypoint_agent._reflection_with_llm(
        messages=chat_history,
        reflection_instruction="You should return the number that represents the restaurant's rating, and absolutely NOTHING else. Just a number."
    )
    """
    result = entrypoint_agent.initiate_chats(
        [
            {
                "recipient": data_fetch_agent,
                "message": user_query,
                "summary_method": "last_msg",
            },
            {
                "recipient": review_agent,
                "message": "Here is the data to convert",
                "summary_method": "last_msg",
            },
            {
                "recipient": scoring_agent,
                "message": "Please give me the score for the following restaurant using the following data: ",
                "summary_method": "last_msg",
                "max_turns": 2,
            }

        ]
    )
    """
    summary = entrypoint_agent.reflect(
        messages=result,
        reflection_instruction="You should return the number that represents the restaurant's rating, and absolutely NOTHING else. Just a number."
    )

    print("THIS IS THE SUMMARY: ")
    print(summary)
    """


    
# DO NOT modify this code below.
if __name__ == "__main__":
    assert len(sys.argv) > 1, "Please ensure you include a query for some restaurant when executing main."
    main(sys.argv[1])