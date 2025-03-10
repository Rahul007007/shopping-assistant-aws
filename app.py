import streamlit as st
import uuid
import requests
from datetime import datetime
import folium
from streamlit_folium import st_folium
from app_utils.maps import calculate_maps_data
import copy

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "shipment_call" not in st.session_state:
    st.session_state.shipment_call = False
if "shipment_details" not in st.session_state:
    st.session_state.shipment_details = None
if "map_data" not in st.session_state:
    st.session_state.map_data = None
if "complete_purchase_call" not in st.session_state:
    st.session_state.complete_purchase_call = False
if "complete_purchase_details" not in st.session_state:
    st.session_state.complete_purchase_details = None
if "cart_items" not in st.session_state:
    st.session_state.cart_items = []
if "purchase_button_clicked" not in st.session_state:
    st.session_state.purchase_button_clicked = False
if "purchase_response" not in st.session_state:
    st.session_state.purchase_response = None

def handle_purchase():
    """Handle purchase button click"""
    st.session_state.purchase_button_clicked = True
    details = st.session_state.complete_purchase_details["response"]["args"]
    details['complete_purchase'] = True
    print("Details:", details)
    purchase_info_response = query_agent(**details)
    print("Purchase Info Response:", purchase_info_response)
    purchase_tool_response = {
        "role": "tool",
        "tool_call_id": st.session_state.complete_purchase_details["response"]["tool_call_id"],
        "content": purchase_info_response["response"]
    }
    final_response = query_agent(**purchase_tool_response)
    st.session_state.purchase_response = final_response["response"]

def query_agent(*args, **kwargs):
    """Send user query to Lambda function and get response"""
    url = "https://uyg4mvttiva6asn2eyuzm5a3ay0pmfdf.lambda-url.ap-south-1.on.aws/"
    
    payload = kwargs.copy()
    payload["session_id"] = st.session_state.session_id
    print("Payload:", payload)  # Debug

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with the agent: {str(e)}")
        raise e
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        raise e

# App title and header
st.title("🛍️ Shopping Assistant")
st.markdown(f"Session ID: `{st.session_state.session_id}`")

if not st.session_state.shipment_call and not st.session_state.complete_purchase_call:
    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Show tools used after assistant messages if tools were used
            if message["role"] == "assistant" and "tools_used" in message and message["tools_used"]:
                with st.expander("🛠️ Tools Used"):
                    for tool in message["tools_used"]:
                        st.markdown(f"- `{tool}`")

    # Chat input
    if prompt := st.chat_input("What would you like to know about our products?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                api_response = query_agent(user_query = prompt)
                if api_response:
                    response = api_response["response"]
                    print("API Response:", api_response)  # Debug print
                    print("Response type:", type(response))  # Debug print
                    
                    if isinstance(response, dict) and "tool_call_id" in response:
                        print("Tool call detected")  # Debug print
                        print("Response details:", response)  # Debug print
                        if response.get("name") == "shipment_details":  # Fixed condition
                            print("Setting shipment call to True")  # Debug print
                            st.session_state.shipment_call = True
                            st.session_state.shipment_details = api_response
                            st.rerun()  # Force refresh to show new UI
                        elif response.get("name") == "complete_purchase":  # Add new condition for buy
                            print("Setting complete purchase call to True")
                            st.session_state.complete_purchase_call = True
                            st.session_state.complete_purchase_details = api_response
                            st.rerun()
                    elif isinstance(response, str):
                        st.markdown(response)
                        message_data = {
                            "role": "assistant", 
                            "content": response
                        }
                        
                        if "tools_used" in api_response and api_response["tools_used"]:
                            message_data["tools_used"] = api_response["tools_used"]
                            with st.expander("🛠️ Tools Used"):
                                for tool in api_response["tools_used"]:
                                    st.markdown(f"- `{tool}`")
                        
                        st.session_state.messages.append(message_data)

    # Optional: Add a button to start a new session
    if st.sidebar.button("New Session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    # Display chat history in sidebar
    with st.sidebar:
        st.markdown("### Chat History")
        for msg in st.session_state.messages:
            st.markdown(f"**{msg['role'].title()}**: {msg['content'][:50]}...")


elif st.session_state.shipment_call:
    print("Shipment call")
    # Clear the previous UI
    st.empty()
    
    # New shipment tracking header
    st.title("📦 Shipment Details")
    st.markdown("Here are the details of your destination")
    # Show tools used if available
    tool_calls = copy.deepcopy(st.session_state.shipment_details.get("tools_used", []))
    tool_calls.append(st.session_state.shipment_details["response"])
    print(st.session_state.shipment_details["response"])
    print("Tool calls:", tool_calls)
    if tool_calls:
        with st.expander("🛠️ Tools Used"):
            for tool in tool_calls:
                st.markdown(f"- `{tool}`")
    
    st.info("Please note that you will be charged $0.01 for every km of the route.")
    # Create two columns for details and map
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Destination Details")
        details = st.session_state.shipment_details["response"]["args"]
        st.write(f"**Destination:** {details["destination"]}")
        # st.write(f"**Order ID:** {st.session_state.session_id[:8]}")
        st.write(f"**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}")

    with col2:
        st.session_state.map_data = calculate_maps_data(**st.session_state.shipment_details["response"]["args"])
        if st.session_state.map_data["source_coords"] and st.session_state.map_data["dest_coords"]:
            try:
                # Calculate map center
                mid_lat = (st.session_state.map_data["source_coords"][0] + 
                        st.session_state.map_data["dest_coords"][0]) / 2
                mid_lon = (st.session_state.map_data["source_coords"][1] + 
                        st.session_state.map_data["dest_coords"][1]) / 2
                
                # Create map with cached data
                m = folium.Map(location=[mid_lat, mid_lon], zoom_start=6)
                
                # Add markers
                folium.Marker(
                    location=st.session_state.map_data["source_coords"],
                    popup="Source",
                    icon=folium.Icon(color="green")
                ).add_to(m)
                
                folium.Marker(
                    location=st.session_state.map_data["dest_coords"],
                    popup="Destination",
                    icon=folium.Icon(color="red")
                ).add_to(m)
                
                # Add route
                if st.session_state.map_data["route"]:
                    folium.PolyLine(
                        st.session_state.map_data["route"],
                        color="blue",
                        weight=5,
                        opacity=0.7
                    ).add_to(m)
                
                # Show map
                st_folium(m, key="persistent_map", width=None, height=400)
                
                # Show route details below map
                st.write(f"**Distance:** {st.session_state.map_data["distance"]/1000:.2f} km")
                st.write(f"**Estimated Duration:** {st.session_state.map_data["duration"]/60:.2f} minutes")

                
                # Add payment options
                st.markdown("---")
                st.markdown("### Choose the options:")
                col_pay1, col_pay2 = st.columns(2)
                
                with col_pay1:
                    button_desc = "Calculate total cost!" 
                    if st.button(button_desc, type="primary"):
                        # First, add the user's action to chat
                        st.session_state.messages.append({"role": "user", "content": button_desc})
                        
                        # Send shipment details to agent
                        maps_tool_response = {
                            "role": "tool",
                            "tool_call_id": st.session_state.shipment_details["response"]["tool_call_id"],
                            "content": f"The shipment needs to delivered to {details['destination']}. The calculated distance: {st.session_state.map_data['distance']/1000:.2f} km."
                        }
                        _ = query_agent(**maps_tool_response)
                        # print("After tool response insertion:", api_response)
                        # tools_after_tool_call = api_response.get("tools_used", [])
                        # Get cost calculation response
                        api_response = query_agent(user_query=button_desc)
                        print("After cost calculation:", api_response)
                        # Add assistant response with tools to chat history
                        # tools_after_tool_call.extend(api_response.get("tools_used", []))
                        message_data = {
                            "role": "assistant",
                            "content": api_response["response"],
                            "tools_used": api_response.get("tools_used", []) #tools_after_tool_call
                        }
                        st.session_state.messages.append(message_data)
                        
                        # Reset states after adding messages
                        st.session_state.shipment_call = False
                        st.session_state.shipment_details = None
                        st.session_state.map_data = None
                        st.rerun()

                with col_pay2:
                    button2_desc = "Add items!"
                    if st.button(button2_desc, type="secondary"):
                        # First, add the user's action to chat
                        st.session_state.messages.append({"role": "user", "content": button2_desc})
                        
                        # Send shipment details to agent
                        maps_tool_response = {
                            "role": "tool",
                            "tool_call_id": st.session_state.shipment_details["response"]["tool_call_id"],
                            "content": f"The shipment needs to delivered to {details['destination']}. The calculated distance: {st.session_state.map_data['distance']/1000:.2f} km. But the user wants to add more items to the cart."
                        }
                        query_agent(**maps_tool_response)
                        
                        # Get buy more response
                        api_response = query_agent(user_query=button2_desc)
                        print("After buy more:", api_response)
                        # Add assistant response with tools to chat history
                        message_data = {
                            "role": "assistant",
                            "content": api_response["response"],
                            "tools_used": api_response.get("tools_used", [])
                        }
                        st.session_state.messages.append(message_data)
                        
                        # Reset states after adding messages
                        st.session_state.shipment_call = False
                        st.session_state.shipment_details = None
                        st.session_state.map_data = None
                        st.rerun()

            except Exception as e:
                st.error(f"Error displaying map: {str(e)}")

elif st.session_state.complete_purchase_call:
    # Clear the UI
    st.empty()
    
    # Show centered buy button
    st.title("🛒 Ready to Purchase?")

    tool_calls = copy.deepcopy(st.session_state.complete_purchase_details.get("tools_used", []))
    tool_calls.append(st.session_state.complete_purchase_details["response"])
    print(st.session_state.complete_purchase_details["response"])
    print("Tool calls:", tool_calls)
    if tool_calls:
        with st.expander("🛠️ Tools Used"):
            for tool in tool_calls:
                st.markdown(f"- `{tool}`")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        details = st.session_state.complete_purchase_details["response"]["args"]
        st.write(f"**Pay :** ${details['total_price']}")
        
        # Use on_click parameter for better click handling
        st.button(
            "Complete Purchase", 
            type="primary", 
            use_container_width=True,
            on_click=handle_purchase,
            disabled=st.session_state.purchase_button_clicked
        )
        
        # Display success message below the button
        if st.session_state.purchase_response:
            st.success(st.session_state.purchase_response)

