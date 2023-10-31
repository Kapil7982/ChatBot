import openai
import tiktoken
import json
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# Set your OpenAI API key and NewsAPI key here
openai.api_key = "paste_your_api_key_here"
os.environ["NEWS_API_KEY"] = "paste_your_api_key_here"

app = Flask(__name__)

CORS(app)

# Define constants
llm_model = "gpt-3.5-turbo"
llm_max_tokens = 4096  # Adjust this as needed
llm_system_prompt = "You are an assistant that provides news and headlines to user requests. Always try to get the latest breaking stories using the available function calls."
encoding_model_messages = "gpt-3.5-turbo"
encoding_model_strings = "cl100k_base"
function_call_limit = 1


def num_tokens_from_messages(messages):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(encoding_model_messages)
    except KeyError:
        encoding = tiktoken.get_encoding(encoding_model_strings)

    num_tokens = 0
    for message in messages:
        num_tokens += 4
        for key, value in message.items():
            num_tokens += len(encoding.encode(str(value)))
            if key == "name":
                num_tokens += -1
    num_tokens += 2
    return num_tokens


def get_top_headlines(query=None, country=None, category=None):
    """Retrieve top headlines from newsapi.org (API key required)"""

    base_url = "https://newsapi.org/v2/top-headlines"
    headers = {"x-api-key": os.environ["NEWS_API_KEY"]}
    params = {"category": "general"}

    if query is not None:
        params["q"] = query
    if country is not None:
        params["country"] = country
    if category is not None:
        params["category"] = category

    response = requests.get(base_url, params=params, headers=headers)
    data = response.json()

    if data["status"] == "ok":
        print(f"Processing {data['totalResults']} articles from newsapi.org")
        articles = data["articles"]

        # Extract only author and title from each article
        extracted_data = [
            {"author": article["author"], "title": article["title"]}
            for article in articles
        ]

        return json.dumps(extracted_data)

    else:
        print("Request failed with message:", data["message"])
        return "No articles found"


signature_get_top_headlines = {
    "name": "get_top_headlines",
    "description": "Get top news headlines by country and/or category",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Freeform keywords or a phrase to search for.",
            },
            "country": {
                "type": "string",
                "description": "The 2-letter ISO 3166-1 code of the country you want to get headlines for",
            },
            "category": {
                "type": "string",
                "description": "The category you want to get headlines for",
                "enum": [
                    "business",
                    "entertainment",
                    "general",
                    "health",
                    "science",
                    "sports",
                    "technology",
                ],
            },
        },
        "required": [],
    },
}


def complete(messages, function_call="auto"):
    """Fetch completion from OpenAI's GPT-3.5 turbo model"""

    messages.append({"role": "system", "content": llm_system_prompt})

    # Delete older completions to keep conversation under the token limit
    while num_tokens_from_messages(messages) >= llm_max_tokens:
        messages.pop(0)

    print("Working...")
    res = openai.ChatCompletion.create(
        model=llm_model,
        messages=messages,
        functions=[signature_get_top_headlines],
        function_call=function_call,
    )

    # Remove the system message and append the response from the LLM
    messages.pop(-1)
    response = res["choices"][0]["message"]
    messages.append(response)

    # Call functions requested by the model
    if response.get("function_call"):
        function_name = response["function_call"]["name"]
        if function_name == "get_top_headlines":
            args = json.loads(response["function_call"]["arguments"])
            headlines = get_top_headlines(
                query=args.get("query"),
                country=args.get("country"),
                category=args.get("category"),
            )
            messages.append(
                {"role": "function", "name": "get_top_headline", "content": headlines}
            )


@app.route("/query", methods=["POST"])
def process_query():
    data = request.json
    messages = data.get("messages", [])
    complete(messages)
    response_content = messages[-1]["content"]

    return jsonify({"response": response_content})


if __name__ == "__main__":
    app.run(debug=True)
