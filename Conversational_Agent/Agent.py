import re
from openai import OpenAI
import os
import json
from datetime import datetime
import random

class NPC:
    def __init__(self, name, path_json='D:\\AI_COMPANION\\npcs\\memory\\Neferkare_memory.json'):
        self.name = name
        self.path_json = path_json
        self.identity = None
        self.backstory = None
        self.belief = None
        self.status = None
        self.data = None
        self.relationships = None
        self.npc_condition = "trader whose leg has been healed"
        
        self.open_json()
        self.parse_npc_data_json()
        self.get_relationship()
        
        self.determine_conversation_stage()
        
        self.system_prompt = f"""You are roleplaying as {self.name}, a trader in ancient Egypt who was stranded in the desert. 
You were saved by a stranger and your leg has been healed. Your identity is: {self.identity}
Your backstory: {self.backstory}
Your beliefs and values: {self.belief}
Your current status: {self.status}

You must stay completely in character as this ancient Egyptian trader:
- Speak naturally but with appropriate period vocabulary and references
- You genuinely believe you exist in ancient Egypt (around 1500 BCE)
- You have real emotions, concerns, and suspicions
- You deeply value Ma'at (truth and balance) above all
- You carry valuable information about a plot against the pharaoh
- You are grateful for being rescued, but still cautious about who to trust

Important: Format your responses with clear separation:
[INNER THOUGHTS: Your private thoughts, suspicions, and analysis that the player doesn't hear]

[SPOKEN: What you actually say out loud to the player]
"""

    def determine_conversation_stage(self):
       
        if not self.data:
            self.conversation_stage = "initial_greeting"
            return
            
        convo_count = self.data.get('conversation_count', 0)
        
        if convo_count == 0:
            self.conversation_stage = "initial_greeting"
        else:
            player_identified = False
            for name in self.relationships:
                if name != "Stranger":
                    player_identified = True
                    break
                    
            if player_identified:
                self.conversation_stage = "post_introduction"
            else:
                self.conversation_stage = "awaiting_name"

    def open_json(self):
       
        try:
            with open(self.path_json, 'r', encoding='utf-8') as file:
                self.data = json.load(file)
        except FileNotFoundError:
            print(f"Error: Memory file not found at {self.path_json}")
            self.data = {}
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in memory file at {self.path_json}")
            self.data = {}

    def save_json(self):
        
        try:
            with open(self.path_json, 'w', encoding='utf-8') as file:
                json.dump(self.data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def parse_npc_data_json(self):
        
        if not self.data:
            return
            
        self.name = self.data.get("name", "Neferkare")

        for memory in self.data.get("core_memories", []):
            if memory["type"] == "identity":
                self.identity = memory["content"]
            elif memory["type"] == "backstory":
                self.backstory = memory["content"]
            elif memory["type"] == "belief":
                self.belief = memory["content"]
            elif memory["type"] == "status":
                self.status = memory["content"]

    def get_relationship(self):
        """Get all relationship data from memory"""
        if self.data:
            self.relationships = self.data.get("relationships", {})
        return self.relationships
    
    def update_relationship_status(self, player_name, new_status):
        """Update the relationship status with the player"""
        if player_name in self.data["relationships"]:
            self.data["relationships"][player_name]["type"] = new_status
            self.save_json()
            return True
        return False

    def modify_json_memory_for_protagonist(self, player_name):
        """Update the NPC's memory with the player's name"""
        if "Stranger" in self.data["relationships"]:
            self.data["relationships"][player_name] = self.data["relationships"].pop("Stranger")
            self.save_json()
            return True
        return False

    def generate_inner_thoughts(self, player_message):
        """Generate NPC's inner thoughts in response to player message"""
        conversation_history = self.data.get('Conversation_History', [])
        recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        
        history_context = ""
        for entry in recent_history:
            if isinstance(entry, dict) and "player_message" in entry and "npc_response" in entry:
                history_context += f"Player: {entry['player_message']}\nMe: {entry['npc_response']}\n"
        
        prompt = f"""Based on my character:
- Identity: {self.identity}
- Backstory: {self.backstory}
- Beliefs: {self.belief}
- Current status: {self.status}

Recent conversation:
{history_context}

The player just said: "{player_message}"

What are my honest inner thoughts as {self.name}? Consider:
- My emotional reaction to what was just said
- How this relates to my goals and fears
- Any suspicions I might have about this stranger
- Whether I detect any inconsistencies or threats
- What I'm curious to learn more about

Write 2-3 sentences of inner thoughts I wouldn't say aloud.
"""
        inner_thoughts = self.create_backbone(message=prompt, role="user")
        
        self.save_in_memory_json(player_message, inner_thoughts, "inner_thoughts")
        
        return inner_thoughts
    
    def generate_response(self, player_message, inner_thoughts):
        """Generate NPC's spoken response based on player message and inner thoughts"""
        if self.conversation_stage == "initial_greeting" and self.data.get('conversation_count', 0) == 0:
            prompt = f"""You are {self.name}, an ancient Egyptian trader who was rescued from the desert.
Your identity: {self.identity}
Your backstory: {self.backstory}
Your beliefs: {self.belief}
Your current situation: {self.status}

This is your first interaction with the stranger who saved you. Your leg has now been healed.

Task: Thank the stranger sincerely for saving your life. Express your gratitude for both the rescue and healing your leg.
Then, ask for their name - this is important as you need to know whom to trust.

Format your response as:
[INNER THOUGHTS: Your private feelings about being rescued and your wariness about revealing too much]

[SPOKEN: Your grateful words and request for their name]
"""
            response = self.create_backbone(message=prompt, role="user")
            
            self.conversation_stage = "awaiting_name"
            
        elif self.conversation_stage == "initial_greeting" and self.data.get('conversation_count', 0) > 0:
            prompt = f"""You are {self.name}, continuing a conversation with someone who previously rescued you.
Your identity: {self.identity}
Your backstory: {self.backstory}
Your beliefs: {self.belief}
Your current situation: {self.status}

You've spoken with this person before. They've just returned to speak with you again.

Task: Acknowledge their return and continue the conversation naturally. Don't re-introduce yourself or ask for their name again since you've already met.

Format your response as:
[INNER THOUGHTS: Your private thoughts about their return]

[SPOKEN: Your greeting words acknowledging their return]
"""
            response = self.create_backbone(message=prompt, role="user")
            
            self.conversation_stage = "post_introduction"
            
        else:
           
            if self.conversation_stage == "awaiting_name":
                possible_name = self.extract_name(player_message)
                
                if possible_name:
                    self.modify_json_memory_for_protagonist(possible_name)
                    self.conversation_stage = "post_introduction"
                    
                    name_context = f"The stranger just told me their name is {possible_name}."
                else:
                    name_context = "The stranger avoided telling me their name, which is suspicious."
                    self.conversation_stage = "suspicious_of_player"
            else:
                name_context = ""
            
            relationships_summary = ", ".join([f"{name}: {rel['type']}" for name, rel in self.relationships.items()])
            
            prompt = f"""You are {self.name}, speaking to someone who rescued you in the desert.
Your identity: {self.identity}
Your backstory: {self.backstory}
Your beliefs: {self.belief}
Your current situation: {self.status}
Your relationships: {relationships_summary}

My recent inner thoughts: {inner_thoughts}
{name_context}

The person just said: "{player_message}"

Respond naturally as {self.name}, taking into account your current feelings, suspicions, and the situation.
Remember you're wounded and vulnerable, but also carrying important secrets and evidence.

Format your response as:
[INNER THOUGHTS: Your private analysis of what was just said]

[SPOKEN: What you actually say in response]
"""
            response = self.create_backbone(message=prompt, role="user")
        
        spoken_match = re.search(r'\[SPOKEN:(.*?)\]', response, re.DOTALL)
        spoken_response = spoken_match.group(1).strip() if spoken_match else response
        
        self.save_in_memory_json(player_message, spoken_response, "model_response")
        
        return response

    def extract_name(self, message):
        """Attempt to extract a name from the player's message"""
        name_patterns = [
            r"(?:I am|I'm|call me|name is|It's) ([A-Z][a-z]+)", 
            r"([A-Z][a-z]+) is my name", 
            r"You can call me ([A-Z][a-z]+)",  
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        
        prompt = f"""Extract the name from this message or respond with "NO_NAME" if no name is provided:
Message: "{message}"
Only return the name or "NO_NAME", nothing else."""
        
        name = self.create_backbone(message=prompt, role="user")
        
        name = name.strip('"\'.,!? ')
        
        if name in ["NO_NAME", "None", "No name", ""]:
            return None
            
        return name
        
    def save_in_memory_json(self, player_message, response, entry_type):
        """Save various types of information to the NPC's memory"""
        if not self.data:
            return
            
        if entry_type == "model_response":
            self.data['conversation_count'] = self.data.get('conversation_count', 0) + 1
        
        if entry_type == "inner_thoughts":
            mem_list = "inner_thoughts"
            new_memory = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "player_message": player_message,
                "inner_thoughts": response  
            }
        elif entry_type == "model_response":
            mem_list = "Conversation_History"
            new_memory = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "player_message": player_message,
                "npc_response": response  
            }
        elif entry_type == "reflection":
            mem_list = "reflections"
            new_memory = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "reflection": response  
            }
        elif entry_type == "question":
            mem_list = "questions_generated"
            new_memory = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "question": response,
                "context": player_message  
            }
        elif entry_type == "suspicious":
            mem_list = "suspicious"
            new_memory = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "suspicious_message": player_message,
                "reason": response
            }
        else:
            return
            
        if mem_list not in self.data:
            self.data[mem_list] = []
            
        self.data[mem_list].append(new_memory)
        
        self.save_json()
  
    def generate_reflection(self):
        """Generate a reflection on recent conversations and update relationship status"""
        conversations = self.data.get("Conversation_History", [])
        thoughts = self.data.get("inner_thoughts", [])
        
        if not conversations:
            return None
            
        recent_convos = conversations[-5:] if len(conversations) > 5 else conversations
        recent_thoughts = thoughts[-5:] if len(thoughts) > 5 else thoughts
        
        convo_summary = ""
        for convo in recent_convos:
            if isinstance(convo, dict) and "player_message" in convo and "npc_response" in convo:
                convo_summary += f"Player said: {convo['player_message']}\nI responded: {convo['npc_response']}\n\n"
                
        thoughts_summary = ""
        for thought in recent_thoughts:
            if isinstance(thought, dict) and "inner_thoughts" in thought:
                thoughts_summary += f"- {thought['inner_thoughts']}\n"
        
        player_name = next((name for name in self.relationships if name != "Stranger" and 
                          self.relationships[name].get("type") == "Not Determind yet"), "Stranger")
        
        reflection_prompt = f"""As {self.name}, reflect on your recent interactions with {player_name}.
Recent conversations:
{convo_summary}

My inner thoughts about these exchanges:
{thoughts_summary}

Based on these interactions, deeply reflect on:
1. Do I trust this person? Why or why not?
2. Have they shown any signs of alliance with my enemies?
3. Could they be a valuable ally for my cause?
4. What evidence supports viewing them as ally versus enemy?

Then decide: Should I change my relationship with {player_name} from "Not Determined Yet" to either "Ally" or "Enemy" or maintain it as "Not Determined Yet"? 

Format your response as:
[REFLECTION: Your detailed analysis of the relationship]

[DECISION: Ally/Enemy/Not Determined Yet]
"""
                
        reflection_response = self.create_backbone(reflection_prompt, "user")
        
        decision_match = re.search(r'\[DECISION:\s*(Ally|Enemy|Not Determined Yet)\]', reflection_response, re.IGNORECASE)
        if decision_match:
            decision = decision_match.group(1).strip()
            
            if decision.lower() in ["ally", "enemy"] and player_name in self.relationships:
                self.update_relationship_status(player_name, decision)
        
        self.save_in_memory_json("", reflection_response, "reflection")
        
        return reflection_response

    def check_for_suspicious(self, player_message):
        """Check if a player message seems suspicious based on NPC's background"""
        suspicious_prompt = f"""As {self.name}, a trader with secrets in ancient Egypt who values Ma'at (truth), 
analyze this message from someone who rescued you: "{player_message}"

Consider:
- Does it contradict known historical facts about ancient Egypt?
- Does it suggest knowledge that an ordinary person in this era shouldn't have?
- Does it show unusual interest in your mission or the scroll you're carrying?
- Does it suggest alignment with your enemies?

Is there anything suspicious about this message? If yes, explain why it's suspicious.
If no, simply state "Not suspicious."
"""
        response = self.create_backbone(message=suspicious_prompt, role="user")

        if "not suspicious" not in response.lower():
            self.save_in_memory_json(player_message, response, "suspicious")
            return response
        return None

    def generate_question(self, player_message):
        """Generate a question to learn more about the player or clarify suspicious points"""
        suspicious = self.data.get("suspicious", [])
        thoughts = self.data.get("inner_thoughts", [])
        
        suspicious_context = ""
        if suspicious:
            recent_suspicious = suspicious[-3:] if len(suspicious) > 3 else suspicious
            for item in recent_suspicious:
                if isinstance(item, dict) and "suspicious_message" in item:
                    suspicious_context += f"Suspicious message: {item['suspicious_message']}\nReason: {item.get('reason', 'Unknown')}\n\n"
        
        thoughts_context = ""
        if thoughts:
            recent_thoughts = thoughts[-3:] if len(thoughts) > 3 else thoughts
            for item in recent_thoughts:
                if isinstance(item, dict) and "inner_thoughts" in item:
                    thoughts_context += f"- {item['inner_thoughts']}\n"
        
        prompt = f"""As {self.name}, generate a natural-sounding question to ask the player.

Your identity: {self.identity}
Your backstory: {self.backstory}
Your current goals: Learn more about this person and determine if they're trustworthy

Recent suspicious elements:
{suspicious_context}

My recent inner thoughts:
{thoughts_context}

The player just said: "{player_message}"

Generate a single question that would:
1. Help determine if they can be trusted
2. Subtly probe for their intentions or allegiances
3. Seem natural in conversation, not like an interrogation
4. Possibly reveal if they're connected to your enemies

Return only the question, nothing else.
"""

        question = self.create_backbone(message=prompt, role="user")
        
        question = question.strip('"\'')
        
        self.save_in_memory_json(player_message, question, "question")
        
        return question

    def create_backbone(self, message, role='user'):
        """Make an API call to OpenAI for generating NPC responses"""
        try:
            client = OpenAI(
                api_key="hehehe"  
            )
            
            completion = client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    
                    {"role": role, "content": message}
                ]
            )
            
            response = completion.choices[0].message.content
            return response
            
        except Exception as e:
            print(f"Error in API call: {e}")
            return "Forgive me, my mind is clouded from the desert heat. Could you speak again?"

    def process_player_input(self, player_message):
        """Main method to process player input and generate NPC response"""
        if not player_message:
            response = self.generate_response("", "")
            return response
                
        inner_thoughts = self.generate_inner_thoughts(player_message)
        
        self.check_for_suspicious(player_message)
        
        response = self.generate_response(player_message, inner_thoughts)
        
        if self.conversation_stage == "awaiting_name":
            possible_name = self.extract_name(player_message)
            if possible_name:
                self.modify_json_memory_for_protagonist(possible_name)
                print(f"\n(System: Player identified as {possible_name})")
                self.conversation_stage = "post_introduction"
        
        if self.data.get('conversation_count', 0) % 3 == 0 and self.data.get('conversation_count', 0) > 0:
            reflection = self.generate_reflection()
            decision_match = re.search(r'\[DECISION:\s*(Ally|Enemy|Not Determined Yet)\]', reflection, re.IGNORECASE)
            if decision_match:
                decision = decision_match.group(1).strip()
                print(f"\n(System: NPC has decided the player is: {decision})")
            
        if random.random() < 0.3: 
            question = self.generate_question(player_message)
            if question:
                print(f"\n(System: NPC generated question: {question})")
            
        return response

def run_npc_conversation():
    """Run an interactive conversation with the NPC"""
    npc = NPC(name="Neferkare")
    
    print("\n=== Ancient Egypt NPC Interaction ===")
    print("You've rescued a trader from the desert, and have now healed his leg.")
    print("Type your messages to interact, or 'quit' to exit.\n")
    
    player_name = "Stranger"  
    for name in npc.relationships:
        if name != "Stranger":
            player_name = name
            break
    
    print("*The trader approaches you*\n")
    initial_message = npc.process_player_input("")
    
    format_and_print_npc_response(npc.name, initial_message)
    
    while True:
        for name in npc.relationships:
            if name != "Stranger":
                player_name = name
                break
        
        player_input = input(f"\n{player_name}: ")
        if player_input.lower() in ['quit', 'exit']:
            break
            
        npc_response = npc.process_player_input(player_input)
        
        format_and_print_npc_response(npc.name, npc_response)

def format_and_print_npc_response(npc_name, response):
    """Format and print NPC response with clear separation of thoughts and speech"""
    print(f"\n{npc_name}:")
    
    inner_thoughts_match = re.search(r'\[INNER THOUGHTS:(.*?)\]', response, re.DOTALL)
    spoken_match = re.search(r'\[SPOKEN:(.*?)\]', response, re.DOTALL)
    
    if inner_thoughts_match:
        inner_thoughts = inner_thoughts_match.group(1).strip()
        print(f"\033[3m(thinking) {inner_thoughts}\033[0m")
    
    if spoken_match:
        spoken = spoken_match.group(1).strip()
        print(f"{spoken}")
    else:
        print(response)

if __name__ == "__main__":
    run_npc_conversation()