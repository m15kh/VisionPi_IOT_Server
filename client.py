import asyncio
import websockets
import json

async def connect_to_server():
    uri = "ws://localhost:20807"
    async with websockets.connect(uri) as websocket:
        try:
            while True:
                # Send a message to the server
                message = "Hello Server!"
                await websocket.send(message)
                print(f"Sent message: {message}")
                
                # Receive the response
                response = await websocket.recv()
                print(f"Received response: {response}")
                
                # Wait before sending next message
                await asyncio.sleep(2)
                
        except websockets.ConnectionClosed:
            print("Connection to server closed")

if __name__ == "__main__":
    asyncio.run(connect_to_server())
