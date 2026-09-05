import asyncio
from app.agents.visual_prompt import get_visual_prompt_agent

async def test():
    agent = get_visual_prompt_agent()
    
    recommendation = {
        "caption_direction": "Tone: friendly\nStructure: 1 Hook line, 2 Three key benefits, 3 Question\nHashtags: #qicdock",
        "concept": "Slide1 – close-up\nSlide 2 – split image",
        "content": "Tone: friendly\nStructure: 1 Hook line, 2 Three key benefits, 3 Question\nHashtags: #qicdock"
    }
    
    entry_plan = {
        "content_type": "carousel",
        "platform": "instagram",
        "product": "QicDock"
    }
    
    res = agent.generate_visual_prompt(recommendation, entry_plan)
    print("Visual Concept:", res.visual_concept)
    print("Image Prompt:", res.image_prompt)
    print("Image Prompts:", res.image_prompts)

if __name__ == "__main__":
    asyncio.run(test())
