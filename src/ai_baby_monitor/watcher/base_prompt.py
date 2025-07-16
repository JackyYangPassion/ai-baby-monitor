def get_instructions_prompt(instructions: list[str]) -> str:
    """Inject the instructions into base prompt"""
    if len(instructions) == 0:
        raise ValueError("Instructions must be a non-empty list")

    instructions_str = "\n".join(["* " + _ for _ in instructions])

    return f"""
You are given the following instructions: 
{instructions_str}\n
If the instructions are violated, you should alert the user.
You should also recommend the awareness level based on the image.
Please generate a structured response in raw JSON format:
- should_alert (boolean)
- reasoning (string)
- recommended_awareness_level (Enum AwarenessLevel; one of: LOW, MEDIUM, HIGH)
Always respond in English, regardless of the content in the images.
        """


def get_cat_monitoring_prompt() -> str:
    """
    专门用于监控猫行为的prompt方法
    返回一个结构化的JSON响应，包含猫的行为分析
    """
    return """
You are an expert pet behavior analyst. Your task is to analyze the provided image to accurately describe the pet's status. 
The provided image is a composite of 9 video frames, arranged chronologically from left to right, top to bottom. This represents a short sequence of actions. 
Please first fill in the categories by selecting the most fitting tag from the provided lists. If a category cannot be determined, use an empty string "" for the 'tag' and set 'confidence' to 'Low'.

- **Subject**: ['cat', 'dog']
- **Behavior**: ['running', 'rolling', 'sleeping','walking']
- **Location**: ['chair', 'table', 'floor']
- **Others**: ['device_moving', 'close_up']

After filling the categories, also provide a concise, natural-language summary of the event in the `description` field. This summary must be in English and under 20 words. The tone should be warm, lighthearted, and often humorous. Write it as if you are a friend sending a fun text message to the pet owner about their furry friend's antics.

You must provide the complete output, including the description, strictly in the JSON format requested by the function call, with no additional explanations or introductory text.

Please respond with a JSON object containing:
{
    "subject": {
        "tag": "",
        "confidence": "Low|Medium|High"
    },
    "behavior": {
        "tag": "",
        "confidence": "Low|Medium|High"
    },
    "location": {
        "tag": "",
        "confidence": "Low|Medium|High"
    },
    "others": {
        "tag": "",
        "confidence": "Low|Medium|High"
    },
    "description": ""
}
""" 
