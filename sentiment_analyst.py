import ollama
import requests
import json
import pandas as pd
import sys
from colorama import Fore, Style, init
from tabulate import tabulate
from datetime import datetime, timedelta
import textwrap
import re

# --- Configuration ---
NEWSAPI_KEY = "3357bfc829fc4f1d906d0d5b72f2980c"
OLLAMA_MODEL = "granite3.3:2b"
QUERY = '("SPY" OR "S&P 5tg00") AND (market OR stocks OR finance OR earnings OR Fed OR inflation OR economy)'
DOMAINS = None

# --- Logger Class ---
class Logger:
    """
    Redirects all console output to both stdout and a log file,
    stripping colors from the file output for readability.
    """
    def __init__(self, filename):
        self.terminal = sys.__stdout__
        self.logfile = open(filename, "w", encoding='utf-8')

    def write(self, message):
        # Write colored output to terminal
        self.terminal.write(message)
        # Strip ANSI color codes before writing to file
        clean_message = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', message)
        self.logfile.write(clean_message)

    def flush(self):
        self.terminal.flush()
        self.logfile.flush()


# --- Initialize colorama ---
init(autoreset=True)


# --- Fetch News Articles ---
def get_top_articles(api_key, query, domains=None):
    print(f"{Fore.CYAN}Fetching recent articles for SPY...{Style.RESET_ALL}")
    today = datetime.now()
    from_date = (today - timedelta(days=2)).strftime('%Y-%m-%d')

    params = {
        'q': query,
        'from': from_date,
        'sortBy': 'relevance',
        'language': 'en',
        'pageSize': 100,
        'apiKey': api_key
    }

    if domains:
        params['domains'] = domains
        print(f"Searching within specific domains: {domains}")

    try:
        response = requests.get("https://newsapi.org/v2/everything", params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        if not articles:
            print(f"{Fore.YELLOW}⚠️  No articles found. Check your query or API key.{Style.RESET_ALL}")
            return []
        print(f"{Fore.GREEN}✅ Successfully fetched {len(articles)} articles.{Style.RESET_ALL}")
        return articles
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error fetching news: {e}{Style.RESET_ALL}")
        try:
            print(f"API Error Details: {response.json().get('message', '')}")
        except Exception:
            pass
        return []


# --- Analyze Sentiment ---
def analyze_sentiment(headline, description):
    """
    Uses Ollama to analyze sentiment and return structured response.
    """
    if not description:
        description = "No description available."

    prompt = f"""
    You are a professional financial analyst specializing in U.S. equity markets. 
    Your task is to assess the *investor sentiment* toward the S&P 500 ETF (SPY) 
    based on the given news headline and description.

    ### Instructions:
    1. **Sentiment Classification**
    - Choose exactly one of: "Positive", "Negative", or "Neutral".
    - Evaluate sentiment from a *market reaction perspective* (not tone or emotion).
        - "Positive": Suggests bullishness, optimism, growth, or upward price movement.
        - "Negative": Suggests bearishness, risk, losses, economic weakness, or uncertainty.
        - "Neutral": Mixed signals, balanced tone, or minimal expected market impact.

    2. **Justification**
    - Provide a concise, factual reason (1-2 sentences max).
    - Base it on *economic or market logic* (not word emotion alone).

    3. **Confidence Score**
    - A decimal between 0 and 1.
    - Reflects how confident you are in your sentiment classification.
    - Example scale:
        - 0.8-1.0 → clear, strong signal
        - 0.5-0.7 → somewhat clear but mixed
        - 0.0-0.4 → unclear or speculative context

    ### Response Format:
    Return your final answer in **strict JSON** with this exact structure:
    {{
    "sentiment": "Positive" | "Negative" | "Neutral",
    "justification": "short explanation here",
    "confidence_score": 0.00
    }}

    ### Data:
    Headline: "{headline}"
    Description: "{description}"
    """

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            format="json"
        )
        return json.loads(response['message']['content'])
    except Exception as e:
        print(f"  -> {Fore.RED}Error analyzing sentiment:{Style.RESET_ALL} {e}")
        return {"sentiment": "Error", "justification": str(e), "confidence_score": 0.0}


# --- Main Function ---
def main():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"sentiment_output_{timestamp}.txt"

    # Redirect stdout to custom logger
    sys.stdout = Logger(log_filename)

    print(f"{Fore.LIGHTBLACK_EX}--- Sentiment Analysis Run: {datetime.now()} ---{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}Log file: {log_filename}{Style.RESET_ALL}\n")

    if not NEWSAPI_KEY:
        print(f"{Fore.RED}⚠️  Please provide your NewsAPI key in the script.{Style.RESET_ALL}")
        return

    articles = get_top_articles(NEWSAPI_KEY, QUERY, domains=DOMAINS)
    if not articles:
        print(f"{Fore.YELLOW}No articles found. Exiting.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}🔍 Starting sentiment analysis on {len(articles)} articles...\n{Style.RESET_ALL}")

    results = []
    for i, article in enumerate(articles, start=1):
        title = article.get('title', '')
        print(f"{Fore.LIGHTBLACK_EX}[{i}/{len(articles)}]{Style.RESET_ALL} {title}")
        description = article.get('description', '')
        sentiment_data = analyze_sentiment(title, description)
        results.append({
            'title': title,
            'source': article.get('source', {}).get('name'),
            'sentiment': sentiment_data.get('sentiment'),
            'justification': sentiment_data.get('justification'),
            'confidence_score': sentiment_data.get('confidence_score')
        })

    df = pd.DataFrame(results)
    print(f"\n{Fore.GREEN}✅ Sentiment analysis complete!\n{Style.RESET_ALL}")

    if df.empty:
        print(f"{Fore.YELLOW}No results to display.{Style.RESET_ALL}")
        return

    # --- Sentiment Summary ---
    print(f"{Fore.CYAN}📊 Sentiment Distribution:\n{Style.RESET_ALL}")
    print(df['sentiment'].value_counts().to_string())

    score_map = {'Positive': 1, 'Neutral': 0, 'Negative': -1, 'Error': 0}
    df['score'] = df['sentiment'].map(score_map)
    df['confidence_score'] = pd.to_numeric(df['confidence_score'], errors='coerce').fillna(0)
    df['weighted_score'] = df['score'] * df['confidence_score']
    avg_weighted = df['weighted_score'].mean()

    sentiment_label = (
        "Leaning Positive" if avg_weighted > 0.15 else
        "Largely Negative" if avg_weighted < -0.15 else
        "Largely Neutral/Mixed"
    )
    color = (
        Fore.GREEN if avg_weighted > 0.15 else
        Fore.RED if avg_weighted < -0.15 else
        Fore.YELLOW
    )

    print(f"\n{color}Average Weighted Sentiment Score: {avg_weighted:.3f}{Style.RESET_ALL}")
    print(f"{color}Overall Sentiment: {sentiment_label}{Style.RESET_ALL}\n")

    # --- Detailed Results ---
    print(f"{Fore.CYAN}🧾 Detailed Results:{Style.RESET_ALL}\n")

    for index, row in df.iterrows():
        wrapped_justification = textwrap.fill(str(row['justification']), width=90)
        print(f"{Fore.WHITE}Title:{Style.RESET_ALL} {row['title']}")
        print(f"{Fore.LIGHTBLUE_EX}Sentiment:{Style.RESET_ALL} {row['sentiment']}")
        print(f"{Fore.LIGHTBLACK_EX}Justification:{Style.RESET_ALL} {wrapped_justification}")
        print(f"{Fore.YELLOW}Confidence:{Style.RESET_ALL} {float(row['confidence_score']):.2f}")
        print("-" * 100)

    print(f"\n{Fore.LIGHTBLACK_EX}Analysis completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
    print("-" * 100)
    print(f"\n💾 Output saved to {Fore.CYAN}{log_filename}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
