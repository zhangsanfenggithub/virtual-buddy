import asyncio
import json
import websockets


async def test():
    ws = await websockets.connect("ws://localhost:8000/ws?speed=60")
    for i in range(3):
        msg = await ws.recv()
        data = json.loads(msg)
        print(f"#{i+1} step={data['step']} time={data['sim_time']} "
              f"glucose={data['glucose']:.1f} status={data['status']}")
    await ws.close()
    print("WebSocket test PASSED!")

asyncio.run(test())
