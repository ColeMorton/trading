import pandas as pd
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_ollama import OllamaLLM
import sys
import httpx

def load_mock_csv(file_path):
    """
    Loads portfolio statistics from a CSV file into a pandas DataFrame.
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        print(f"Error: Could not find file at {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading CSV file: {str(e)}")
        sys.exit(1)

def create_langchain_agent(df):
    """
    Creates a LangChain agent that can handle data from the dataframe using Ollama LLM.
    """
    try:
        # Use Ollama's local LLaMA instance
        llm = OllamaLLM(
            model="llama3.2:latest",  # Changed to llama2 as it's more commonly available
            base_url="http://localhost:11434",
            temperature=1
        )
        
        # Create an agent that interacts with the dataframe
        agent = create_pandas_dataframe_agent(
            llm, 
            df, 
            allow_dangerous_code=True,
            verbose=True
        )
        
        return agent
    except httpx.ConnectError:
        print("""
Error: Could not connect to Ollama server.

Please ensure:
1. Ollama is installed (https://ollama.ai)
2. Ollama server is running (run 'ollama serve' in terminal)
3. The llama2 model is pulled (run 'ollama pull llama2')
4. Port 11434 is available and not blocked by firewall
        """)
        sys.exit(1)
    except Exception as e:
        print(f"Error creating LangChain agent: {str(e)}")
        sys.exit(1)

def analyze_portfolio(agent, question):
    """
    Passes the portfolio statistics data to the agent with a question.
    """
    try:
        result = agent.invoke(question)  # Using invoke instead of deprecated run
        return result
    except Exception as e:
        print(f"Error analyzing portfolio: {str(e)}")
        sys.exit(1)

def main():
    # File path for portfolio statistics
    file_path = 'csv/strategies/portfolio_d_20250510.csv'
    
    print("Loading portfolio data...")
    df = load_mock_csv(file_path)
    
    print("Creating LangChain agent...")
    agent = create_langchain_agent(df)
    
    print("Analyzing portfolio...")
    question = "The data provided is a collection of EMA cross trading strategies. The short window and long window of each strategy is unique. Anaylze the trading strategies and cross comparison. Identify key metrics and performance indicators that provide insights into its overall health and potential for returns. Generate an in-depth summary of your findings and provide recommendations. Refer to each stratetgy by it's short and long window."
    result = analyze_portfolio(agent, question)
    
    print("\nAnalysis Results:")
    print("-" * 80)
    print(result)
    print("-" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)
