import socket
import json
import time
import threading
from collections import deque

PORT = 5000
BROADCAST_INTERVAL = 0.03  # 30 milliseconds

clients = {}
next_id = 1
actions_queue = deque()
actions_lock = threading.Lock()


def send_data(addr, data):
    """Sends JSON-encoded data to the client at the specified address."""
    try:
        print(f"Sending data: {data} to {addr}")
        sock.sendto(json.dumps(data).encode(), addr)
    except OSError as e:
        print(f"Error sending data to {addr}: {e}")
        if addr in clients:
            print(f"Removing client {clients[addr]['id']} due to send error.")
            del clients[addr]


def notify_about_new_player(client_id, position):
    """Notifies all clients about a new player."""
    for client in clients.values():
        if client["id"] == client_id:
            continue
        message = {"type": "new_player", "id": client_id, "position": position}
        send_data(client["addr"], message)


def send_id(addr, client_id, position):
    """Sends the client ID to the address."""
    response = {"type": "id", "id": client_id}
    print(f"Sending ID: {client_id}")
    send_data(addr, response)
    notify_about_new_player(client_id, position)


def find_client(addr):
    """Finds and returns the client data for a given address, or None if not found."""
    return clients.get(addr)


def notify_about_old_players(addr):
    for client in clients.values():
        print(client, addr)
        if client["addr"] != addr:
            message = {
                "type": "old_player",
                "id": client["id"],
                "position": client["position"],
            }
            send_data(addr, message)


def process_data(addr, data):
    global next_id
    global actions_queue
    print(f"Processing data: {data}")
    data_type = data.get("type")
    client_id = data.get("id")
    print(f"Type: {data_type}")

    if data_type is None:
        print(f"Invalid data received: {data}")
        return

    if data_type == "id":
        position = data.get("position")
        client = find_client(addr)
        if client is None:
            # New client, assign an ID
            clients[addr] = {"id": next_id, "addr": addr, "position": position}
            send_id(addr, next_id, position)
            notify_about_old_players(addr)
            next_id += 1
        else:
            # Existing client, resend ID
            send_id(addr, client["id"], position)
            notify_about_old_players(addr)
    elif data_type == "actions":
        actions = data.get("actions")
        timestamp = data.get("timestamp")
        print(f"Actions array length: {len(actions)}")
        print(f"Timestamp: {timestamp}")

        with actions_lock:
            for action in actions:
                type = action.get("type")
                action_data = action.get("data")
                print(f"Processing action: {action}")
                print(f"Request type: {type}")
                print(f"Data: {action_data}")

                if type == "move":
                    if action_data and "position" in action_data:  # Ensure position exists
                        combined_data = {
                            "data": action_data,
                            "id": client_id,
                            "timestamp": timestamp,
                            "type": "move",
                        }
                        print(f"Combined data: {combined_data}")

                        # Check if there is an older (timestamp) move with the same id, remove it and add this one
                        actions_queue = deque(
                            [
                                a
                                for a in actions_queue
                                if not (a["id"] == client_id and a["timestamp"] < timestamp)
                            ]
                        )
                        actions_queue.append(combined_data)
                        client = find_client(addr)
                        if client:
                            client["position"] = action_data.get("position")
                    else:
                        print(f"Warning: No position found in move action: {action}")

                if type == "action":
                    combined_data = {
                        "type": "action",
                        "data": {
                            "data": action_data,
                            "id": client_id,
                            "timestamp": timestamp,
                            "type": "emit_particles",
                        },
                    }
                    print(f"Combined data: {combined_data}")
                    send_to_everyone_except(addr, combined_data)



def send_to_everyone_except(addr, data):
    print(f"Sending data to everyone except {addr}")
    for client in clients.values():
        if client["addr"] != addr:
            send_data(client["addr"], data)


def broadcast_actions():
    global actions_queue
    with actions_lock:
        if not actions_queue:
            return

        response = {
            "type": "update",
            "data": list(actions_queue),
            "timestamp": int(time.time() * 1000),
        }
        print(f"Broadcasting actions: {response}")
        print(clients, clients.values())
        for client in list(clients.values()):  # Use list() to avoid RuntimeError
            print(f"Sending data to client {client['id']}")
            send_data(client["addr"], response)

        actions_queue.clear()


running = True


def broadcast_thread():
    """Periodically broadcasts updates to all clients."""
    while running:
        time.sleep(BROADCAST_INTERVAL)
        broadcast_actions()


def setup_server():
    """Initializes the UDP socket server."""
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))
    print(f"Server started on port {PORT}. Ready to receive data!")

    # Set a timeout so we don't block forever
    sock.settimeout(1)


def handle_incoming_data():
    """Handles receiving and processing incoming data from clients."""
    while running:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"Received data from {addr}: {data}")
            try:
                json_data = json.loads(data.decode())
                print(f"Received JSON: {json_data}")
                process_data(addr, json_data)
            except json.JSONDecodeError:
                print(f"Invalid JSON received: {data}")
        except socket.timeout:
            pass
        except OSError as e:
            # Handle socket errors like connection reset
            print(f"Socket error: {e}. Ignoring and continuing.")


def main():
    """Main server loop to set up the server and manage incoming data."""
    print("Starting server initialization...")

    # Initialize server socket and start the broadcast thread
    setup_server()

    # Create a thread for broadcasting actions
    broadcast_thread_instance = threading.Thread(target=broadcast_thread)
    broadcast_thread_instance.daemon = True
    broadcast_thread_instance.start()

    # Create a thread to handle incoming data from clients
    data_thread_instance = threading.Thread(target=handle_incoming_data)
    data_thread_instance.daemon = True
    data_thread_instance.start()

    try:
        # Main thread can be used to handle shutdown or other tasks if needed
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        global running
        running = False
        sock.close()
        broadcast_thread_instance.join()
        data_thread_instance.join()
        print("Server shut down gracefully.")


if __name__ == "__main__":
    main()
