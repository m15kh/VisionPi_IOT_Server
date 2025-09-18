import asyncio
import websockets
import json

async def handle_client(websocket):
    try:
        while True:
            # Wait for message from client
            message = await websocket.recv()
            print(f"Received message: {message}")
            
            # Echo the message back
            response = {"status": "ok", "message": f"Server received: {message}"}
            await websocket.send(json.dumps(response))
            
    except websockets.ConnectionClosed:
        print("Client disconnected")

async def main():
    server = await websockets.serve(handle_client, "0.0.0.0", 20807)
    print("WebSocket server started on ws://0.0.0.0:20807")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
