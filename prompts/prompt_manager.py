from typing import Dict, Any
from .base_prompts import (
    OPENAI_BASE_PROMPT,
    ANTHROPIC_BASE_PROMPT,
    GOOGLE_BASE_PROMPT,
    CONCLUSION_BASE_PROMPT,
    FINAL_CONCLUSION_PROMPT
)
from .round2_prompts import ROUND2_TEMPLATE, CHARACTER_SETTINGS

class PromptManager:
    @staticmethod
    def get_display_names() -> dict:
        return {
            agent_type: settings["display_name"]
            for agent_type, settings in CHARACTER_SETTINGS.items()
        }
    @staticmethod
    def get_prompt(agent_type: str, topic: str, relevant_data: Dict = None) -> str:
        prompts = {
            "openai": OPENAI_BASE_PROMPT,
            "anthropic": ANTHROPIC_BASE_PROMPT,
            "google": GOOGLE_BASE_PROMPT,
            "conclusion": CONCLUSION_BASE_PROMPT
        }
        base_prompt = prompts.get(agent_type, "")
        
        if relevant_data:
            data_context = """
            以下のデータを参考に議論してください：
            
            ニュース記事：
            {}
            
            市場データ：
            {}
            """.format(
                "\n".join([f"- {article['title']}" for article in relevant_data.get("news", [])[:3]]),
                "\n".join([f"- {k}: {v.tail(1)}" for k, v in relevant_data.get("market_data", {}).items()])
            )
            base_prompt = base_prompt + "\n" + data_context
        
        return base_prompt.format(topic=topic)

    @staticmethod
    def get_round2_prompt(agent_type: str, conclusion_content: str) -> str:
        character_setting = CHARACTER_SETTINGS.get(agent_type, {})
        if not character_setting:
            return ""
            
        return ROUND2_TEMPLATE.format(
            conclusion=conclusion_content,
            character=character_setting["name"],
            character_prompt=character_setting["prompt"]
        )
    @staticmethod
    def format_conclusion_prompt(opinions: Dict[str, Any], round_num: int = 1) -> str:
        display_names = PromptManager.get_display_names()
        participants_str = "、".join(display_names.values())
        
        if round_num == 1:
            prompt = CONCLUSION_BASE_PROMPT.format(
                round_type="第1ラウンド",
                participants=participants_str,
                opinions=opinions
            )
        else:
            prompt = FINAL_CONCLUSION_PROMPT.format(
                participants=participants_str,
                opinions=opinions
            )
        return prompt