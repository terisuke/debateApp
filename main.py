import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import GoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from prompts import PromptManager
from typing import Dict, Any
from utils.data_searcher import DataSearcher

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
                relevant_data: Dict, round_num: int = 1,
                previous_conclusion: str = None) -> dict:
    """Get opinions from all agents"""
    opinions = {}
    
    for agent_name, agent in agents.items():
        if agent_name != "conclusion":
            if round_num == 1:
                prompt = prompt_manager.get_prompt(agent_name, topic, relevant_data)
            else:
                prompt = prompt_manager.get_round2_prompt(agent_name, previous_conclusion)
            
            opinion = agent.invoke([{"role": "user", "content": prompt}])
            print_opinion(agent_name, opinion, round_num)
            opinions[agent_name] = opinion
    
    return opinions

def print_opinion(agent_name: str, opinion: Any, round_num: int):
    display_names = PromptManager.get_display_names()
    display_name = display_names.get(agent_name, agent_name)
    print(f"=== {display_name}の意見 その{round_num} ===")
    print(opinion.content if hasattr(opinion, 'content') else opinion)

def get_relevant_data(topic: str, data_searcher: DataSearcher) -> Dict:
    """トピックに関連するデータを収集"""
    data = {
        "news": data_searcher.search_news(topic),
        "market_data": {},
        "web_data": []
    }
    
    # トピックに応じて必要なデータを取得
    if "株価" in topic or "投資" in topic:
        data["market_data"] = {
            "nikkei": data_searcher.get_stock_data("^N225"),
            "topix": data_searcher.get_stock_data("^TPX")
        }
    
    return data

def save_debate_to_markdown(topic: str, round1_opinions: dict, round1_conclusion: str, 
                          round2_opinions: dict, final_conclusion: str):
    """議論の内容をMarkdownファイルとして保存"""
    content = f"""# 議論テーマ：{topic}

## 第1ラウンド

### 各参加者の意見
"""
    display_names = PromptManager.get_display_names()
    
    # Round 1の意見を追加
    for agent_name, opinion in round1_opinions.items():
        display_name = display_names.get(agent_name, agent_name)
        content += f"\n#### {display_name}の意見\n"
        content += f"{opinion.content if hasattr(opinion, 'content') else opinion}\n"
    
    # Round 1のまとめを追加
    content += "\n### 第1ラウンドのまとめ\n"
    content += f"{round1_conclusion}\n"
    
    # Round 2の意見を追加
    content += "\n## 第2ラウンド\n\n### 各参加者の意見\n"
    for agent_name, opinion in round2_opinions.items():
        display_name = display_names.get(agent_name, agent_name)
        content += f"\n#### {display_name}の意見\n"
        content += f"{opinion.content if hasattr(opinion, 'content') else opinion}\n"
    
    # 最終まとめを追加
    content += "\n### 最終まとめ\n"
    content += f"{final_conclusion}\n"
    
    # ファイル名に日時を追加して保存
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"debate_{timestamp}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"\n議論の内容を {filename} に保存しました。")

def main():
    # Initialize
    agents = initialize_agents()
    prompt_manager = PromptManager()
    data_searcher = DataSearcher(os.getenv("NEWS_API_KEY"))
    # トピック(ここで話題を決める)
    topic = "アメリカの株式市場と日本の株式市場を比較して、今後の展望について"
    
    # データ収集
    relevant_data = get_relevant_data(topic, data_searcher)
    
    # Round 1 with data
    print(f"\n=== トピック: {topic} ===")
    print("\n=== 第1ラウンド ===")
    round1_opinions = get_opinions(agents, prompt_manager, topic, relevant_data, round_num=1)
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
        relevant_data,
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
    
    # 議論内容をMarkdownファイルとして保存
    save_debate_to_markdown(
        topic,
        round1_opinions,
        round1_conclusion.content,
        round2_opinions,
        final_conclusion.content
    )

if __name__ == "__main__":
    main()