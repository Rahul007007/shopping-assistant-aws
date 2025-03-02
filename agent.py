from typing import Dict, Any, Callable, Tuple, Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
import boto3
import json
import uuid
import traceback
from utils.vector_db import VectorDB, VectorDBConfig
from utils.add_to_cart import add_to_cart
from utils.shipment_details import shipment_details
from utils.complete_purchase import complete_purchase
from utils.calculate_total_price import calculate_total_price
from schemas import Get_Product_Recommendations, Add_To_Cart, Shipment_Details, Calculate_Total_Price, Complete_Purchase
from utils.logger import CustomLogger
from utils.tools import ToolRegistry

logger = CustomLogger("agent")


def initialize_tools(*args, **kwargs) -> ToolRegistry:
    """Initialize and configure all tools"""
    load_dotenv()

    pinecone_api_key = os.getenv("PINECONE_API_KEY")

    # Initialize vector DB
    config = VectorDBConfig(api_key=pinecone_api_key)
    vector_db = VectorDB(config)
    
    # Create and register tools
    tools = ToolRegistry()
    tools.register(vector_db.get_product_recommendations, Get_Product_Recommendations)
    tools.register(add_to_cart, Add_To_Cart)
    tools.register(shipment_details, Shipment_Details)
    tools.register(calculate_total_price, Calculate_Total_Price)
    tools.register(complete_purchase, Complete_Purchase)

    return tools


class Agent:
    def __init__(self, *args, **kwargs):
        try:
            self.tools = initialize_tools()
            self.tool_schema = self.tools.get_all_tool_schemas()
        
            self.client = OpenAI(
                api_key = os.getenv('OPENAI_API_KEY')
            )
        except Exception as e:
            logger.log_trace(f"Error initializing agent: {str(e)}", level="ERROR")
            traceback.print_exc()
            raise e
        # self.messages_file = "session_messages.json"
        self.prompt_file_path = os.path.join(os.path.dirname(__file__), 'prompts', "react_prompt.txt")
        with open(self.prompt_file_path, 'r') as file:
            self.system_prompt = file.read()
        self.model = "gpt-4o-mini"
        self.fallback_model = "gpt-4o" if self.model == "gpt-4o-mini" else "gpt-4o-mini"
        self.dynamodb = boto3.client('dynamodb')

    def __call_llm(self, messages: Dict[str, Any], model: str = "gpt-4o-mini") -> Any:
        """Call LLM with messages and return response"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages = messages,
                tools=self.tool_schema,
                tool_choice="auto",
                temperature=0,
                parallel_tool_calls=True
            )

            return response
        except Exception as e:
            logger.log_trace(f"Error calling LLM: {str(e)}", level="WARNING")
            logger.log_trace(f"Using fallback model: {self.fallback_model}", level="WARNING")
            try:
                return self.__call_llm(messages, model=self.fallback_model)
            except Exception as e:
                logger.log_trace(f"Error calling fallback LLM: {str(e)}", level="ERROR")
                traceback.print_exc()
                raise e
    
    def __decide(self):
        """Decide and generate LLM Response"""
        response_message = self.__call_llm(self.messages).choices[0].message
        content = response_message.content
        tool_calls = response_message.tool_calls
        if content:
            logger.log_trace(f"Response from LLM: {content}", level="DEBUG")
            return content
        elif tool_calls:
            for tool_call in tool_calls:
                name = tool_call.function.name.lower()
                tool_call_id = tool_call.id
                args = json.loads(tool_call.function.arguments)
                self.messages.append({"role": "assistant", "tool_calls": [tool_call.model_dump()]})
                logger.log_trace(f"Tool called: {name} with arguments: {args}", level="DEBUG")
                ### Logic for inputs from UI
                if name == "shipment_details" or name == "complete_purchase":
                    return {"tool_call_id": tool_call_id,"name": name, "args": args}
                result = self.tools.call_function(name, args)# call_function(name, args)
                self.tools_used.append({"tool_call_id": tool_call_id,"name": name, "args": args, "tool_output": result})
                logger.log_trace(f"Response from tool {name}: {result}", level="DEBUG")
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": str(result)
                })
            return self.__decide()
        
    def __get_session_messages(self, session_id: str):
        """Get all messages from DDB"""
        response = self.dynamodb.get_item(
                        TableName='expedite-commerce-assignment',
                        Key={'session_id': {'S': session_id}}
                        )
    
        # Extract messages
        item = response.get('Item', {})
        messages = []

        if 'messages' in item:
            for msg in item['messages']['L']:
                msg_data = msg['M']
                parsed_message = {'role': msg_data['role']['S']}
                
                # If content exists, add it; otherwise, assume it's a tool call structure
                if 'content' in msg_data:
                    parsed_message['content'] = msg_data['content']['S']
                else:
                    parsed_message['tool_calls'] = [
                        json.loads(tc['S']) for tc in msg_data['tool_calls']['L']
                    ]

                # Extract tool_call_id if available
                if 'tool_call_id' in msg_data:
                    parsed_message['tool_call_id'] = msg_data['tool_call_id']['S']
                
                messages.append(parsed_message)

        return messages

    def __save_session_messages(self, session_id: str):
        """Save all messages to DDB"""
        try:
            serialized_messages = []
            
            for msg in self.messages:
                message_item = {'M': {'role': {'S': msg['role']}}}

                # If 'content' exists, store it
                if 'content' in msg:
                    message_item['M']['content'] = {'S': msg['content']}
                
                # If 'tool_call_id' exists, store it
                if 'tool_call_id' in msg:
                    message_item['M']['tool_call_id'] = {'S': msg['tool_call_id']}
                
                # If 'tool_calls' exists, store it as a list of JSON-encoded strings
                if 'tool_calls' in msg:
                    message_item['M']['tool_calls'] = {
                        'L': [{'S': json.dumps(tc)} for tc in msg['tool_calls']]
                    }

                serialized_messages.append(message_item)
            
            # Insert/Update the item in DynamoDB
            self.dynamodb.put_item(
                TableName='expedite-commerce-assignment',
                Item={
                    'session_id': {'S': session_id},
                    'messages': {'L': serialized_messages}
                }
            )
            logger.log_trace(f"Session messages saved successfully", level="DEBUG")
        except Exception as e:
            logger.log_trace(f"Error saving session messages: {str(e)}", level="ERROR")
            traceback.print_exc()
            raise e

    def run(self, body) -> Dict[str, str]:
        """Run the agent with the given body"""
        user_query = body.get("user_query")
        session_id = body.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            self.messages = [{"role": "system", "content": self.system_prompt}]
            logger.log_trace(f"Created new session ID: {session_id}", level="DEBUG")
        else:
            self.messages = self.__get_session_messages(session_id)
            if self.messages:
                logger.log_trace(f"Loaded existing session: {session_id}", level="DEBUG")
                logger.log_trace(f"Loaded session records: {self.messages}", level="DEBUG")
            else: # sessionId is not there then re-initialize
                self.messages = [{"role": "system", "content": self.system_prompt}]
                logger.log_trace(f"Session not found, creating new session with ID: {session_id}", level="DEBUG")

        self.tools_used = []
        if user_query:
            self.messages.append({"role": "user", "content": user_query})
            logger.log_trace(f"Processing user query: {user_query}", level="DEBUG")
        elif "tool_call_id" in body:
            body.pop("session_id")
            self.messages.append(body)

        
        response = self.__decide()
        logger.log_trace(f"Generated response: {response}", level="DEBUG")
        
        if not isinstance(response, dict) and "tool_call_id" not in response: # for UI inputs
            self.messages.append({"role": "assistant", "content": response})
        
        # Save session state
        self.__save_session_messages(session_id)
        
        return {"response": response, "session_id": session_id, "tools_used": self.tools_used}
