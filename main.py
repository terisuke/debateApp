import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import GoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from prompts import PromptManager
from typing import Dict,Any

def initialize_agents():
    """Initialize AI agents"""
    load_dotenv()
    return {
        "openai": ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        ),
        "anthropic": ChatAnthropic(
            model="claude-3-5-sonnet-20240620",
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        ),
        "google": GoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        ),
        "conclusion": ChatOpenAI(
            model="o1-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    }

def get_opinions(agents: dict, prompt_manager: PromptManager, topic: str, 
                round_num: int = 1, previous_conclusion: str = None) -> dict:
    """Get opinions from all agents"""
    opinions = {}
    
    for agent_name, agent in agents.items():
        if agent_name != "conclusion":
            if round_num == 1:
                prompt = prompt_manager.get_prompt(agent_name, topic)
            else:
                prompt = prompt_manager.get_round2_prompt(agent_name, previous_conclusion)
            
            opinion = agent.invoke([{"role": "user", "content": prompt}])
            print_opinion(agent_name, opinion, round_num)  # 変更箇所
            opinions[agent_name] = opinion
    
    return opinions

def print_opinion(agent_name: str, opinion: Any, round_num: int):
    display_names = PromptManager.get_display_names()
    display_name = display_names.get(agent_name, agent_name)
    print(f"\n{display_name}の意見 その{round_num}")
    print(opinion.content if hasattr(opinion, 'content') else opinion)

def main():
    # Initialize
    agents = initialize_agents()
    prompt_manager = PromptManager()
    topic = "ペットは物か家族か"

    # Round 1
    print("\n=== 第1ラウンド ===")
    round1_opinions = get_opinions(agents, prompt_manager, topic, round_num=1)
    round1_conclusion_prompt = prompt_manager.format_conclusion_prompt(round1_opinions, 1)
    round1_conclusion = agents["conclusion"].invoke([{
        "role": "user",
        "content": round1_conclusion_prompt
    }])
    print("\n=== 第1ラウンドのまとめ ===")
    print(round1_conclusion.content)

    # Round 2
    print("\n=== 第2ラウンド ===")
    round2_opinions = get_opinions(
        agents, 
        prompt_manager, 
        topic, 
        round_num=2, 
        previous_conclusion=round1_conclusion.content
    )
    
    # Final Conclusion
    final_opinions = {
        "Round1": round1_opinions,
        "Round2": round2_opinions
    }
    final_conclusion_prompt = prompt_manager.format_conclusion_prompt(final_opinions, 2)
    final_conclusion = agents["conclusion"].invoke([{
        "role": "user",
        "content": final_conclusion_prompt
    }])
    
    print("\n=== 最終まとめ ===")
    print(final_conclusion.content)

if __name__ == "__main__":
    main()