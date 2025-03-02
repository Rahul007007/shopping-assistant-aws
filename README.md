# Expedite Commerce Assignment - AWS

## Overview
This project implements an AI-powered e-commerce assistant deployed on AWS Lambda that helps customers with product recommendations, shopping cart management, shipment calculation, and order processing. The system leverages a ReAct (Reasoning and Action) agent powered by OpenAI's models to interpret user queries and perform appropriate actions through a set of specialized tools.

## Demo & Documentation
- **App Demo**: [Watch Demo Video](https://www.loom.com/share/2a4ad8fd9d1944de907c646b2e811846?sid=2fca7f33-e04c-45ff-a3bf-dffbd56da559)
- **Architecture Diagram**: [View on Miro](https://miro.com/app/board/uXjVIXKzBFg=/?share_link_id=836653816402)
- **Code & Architecture Explanation**: [Watch Explanation Video](https://www.loom.com/share/f3eb50cfdfab4491aa4656df55d2c23d?sid=978a7215-9c93-4365-b8c2-e1257006486f)

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

### Product Recommendations
- Search and suggest products based on natural language queries
- Semantic understanding of user intent
- Presents options with relevant details like pricing and discounts

### Shopping Cart Management
- Add products to cart with specified quantities

### Order Processing
- Calculate shipping distances and costs using geolocation
- Calculate total costs including products, quantities, and shipping
- Complete purchases with order confirmation

### Session Management
- Maintain conversational context across interactions
- Persistent storage of session state in DynamoDB
- Stateful interactions for a seamless user experience

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

### AWS Deployment
1. Create a Lambda layer with required dependencies
2. Create a DynamoDB table named `expedite-commerce-assignment` with primary key `session_id`