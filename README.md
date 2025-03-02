# Expedite Commerce Assignment - AWS

## Overview
This project is an AI-powered e-commerce assistant deployed on AWS Lambda that helps customers with product recommendations, shopping cart management, shipment calculation, and order processing. The system uses a ReAct (Reasoning and Action) agent powered by OpenAI's models to interpret user queries and perform appropriate actions through a set of tools.

## Architecture

### Components
1. **AI Agent**: ReAct agent that processes user queries, reasons about required actions, and calls appropriate tools
2. **Lambda Function**: AWS Lambda endpoint that handles API requests and responses
3. **Vector Database**: Pinecone vector database for semantic product search and recommendations
4. **DynamoDB**: Stores conversation history and session state
5. **Utility Functions**: Various tools for e-commerce operations

### Flow
1. User submits a query to the Lambda endpoint
2. The agent interprets the query using OpenAI's models
3. Based on the interpretation, the agent calls appropriate tools
4. The response is returned to the user and session state is maintained

## Features
- **Product Recommendations**: Search and suggest products based on natural language queries
- **Shopping Cart Management**: Add products to cart with specified quantities
- **Shipment Details**: Calculate shipping distances and costs using geolocation
- **Order Processing**: Calculate total costs and complete purchases
- **Conversational History**: Maintain context across interactions using session management

## Project Structure
```
expedite-commerce-assignment-aws/
├── agent.py                 # Main ReAct agent implementation
├── lambda_function.py       # AWS Lambda handler
├── schemas.py               # Pydantic models for data validation
├── app_utils/               # Application utilities
│   └── maps.py              # Geolocation and routing utilities
├── prompts/                 # LLM prompt templates
│   └── react_prompt.txt     # ReAct agent system prompt
├── utils/                   # Tool implementations
│   ├── add_to_cart.py       # Cart management functions
│   ├── calculate_total_price.py # Price calculation logic
│   ├── complete_purchase.py # Order finalization
│   ├── shipment_details.py  # Shipment processing
│   ├── logger.py            # Logging utilities
│   ├── tools.py             # Tool registry system
│   └── vector_db.py         # Vector database interface
```

## Setup Instructions

### Prerequisites
- AWS Account with Lambda and DynamoDB access
- Python 3.9+
- OpenAI API Key
- Pinecone API Key

### Environment Variables
Create a `.env` file with the following variables:
```
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
```

### Local Development
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run tests or local development server

### AWS Deployment
1. Create a Lambda layer with required dependencies
2. Create a DynamoDB table named `expedite-commerce-assignment` with primary key `session_id`
3. Deploy the code to Lambda:
   ```
   zip -r function.zip . -x "venv/*" -x "*.git*" -x "__pycache__/*" -x "*.zip"
   aws lambda update-function-code --function-name expedite-commerce --zip-file fileb://function.zip
   ```
4. Configure Lambda environment variables

## Usage Examples

### Product Recommendations
```json
{
  "user_query": "I'm looking for running shoes",
  "session_id": "optional-existing-session-id"
}
```

### Add to Cart
```json
{
  "user_query": "Add Nike Air Max to my cart",
  "session_id": "existing-session-id"
}
```

### Complete Purchase
```json
{
  "user_query": "Complete my purchase",
  "session_id": "existing-session-id"
}
```

## API Reference

### Request Format
```json
{
  "user_query": "string",
  "session_id": "string (optional)"
}
```

### Response Format
```json
{
  "user_query": "string",
  "response": "string or object",
  "tools_used": "array of tool calls",
  "session_id": "string"
}
```

## License
[Specify License]