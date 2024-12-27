extends Node

var udp_peer: PacketPeerUDP = PacketPeerUDP.new()
@export var ip: String = "94.228.115.216"
@export var port: int = 5000
var starting_position = Vector2(randf()*300-150, randf()*300-150)
var json: JSON = JSON.new()
func request_id() -> void:
	send_data({
		"id": -1,
		"type": "id",
		"position": {
			"x": starting_position.x,
			"y": starting_position.y
		}
	})

func packet_received(data: Dictionary) -> void:
	if data["type"] == "id":
		on_got_id(data["id"])
	elif data["type"] == "update":
		on_update(data)
	elif data["type"] == "new_player" or data["type"] == "old_player":
		print(data, " ", players)
		var id = int(data["id"])
		if not players.has(id):
			new_player(id, false, data["position"])
	elif data["type"] == "action":
		on_action(data)
var players = {}

func on_action(data: Dictionary) -> void:
	var id = int(data["data"]["id"])
	players[id].get_child(0).handle_response(data)

func on_update(data: Dictionary) -> void:
	for data_i in data["data"]:
		var id = int(data_i["id"])  # Convert to integer to ensure matching types
		if players.has(id):
			print("Found player with ID: ", id)
			players[id].get_child(0).handle_response(data_i)
		else:
			print("Player not found, creating new player with ID: ", id)
			new_player(id, false)

func _ready() -> void:
	connect_udp()
	request_id()

func new_player(id: int, is_local: bool, position = starting_position) -> void:
	print("Creating player with ID: ", id)
	#create player
	var player = load("res://player.tscn").instantiate()
	player.is_local = is_local
	player.get_child(0).id = id
	player.ready()
	player.send_data.connect(send_data)
	player.set_name("Player%d" % id)
	print(position)
	player.get_child(0).position = Vector2(position["x"], position["y"])
	get_parent().add_child(player)

	players[id] = player

func on_got_id(id: int) -> void:
	new_player(id, true)
	

func connect_udp() -> void:
	udp_peer.connect_to_host(ip, port)
	print("Connected to %s:%d" % [ip, port])

func send_data(packet: Dictionary) -> void:
	var data = json.stringify(packet)
	udp_peer.put_packet(data.to_ascii_buffer())
	print ("Sent: ", data)

func _process(_delta: float) -> void:
	if udp_peer.get_available_packet_count() > 0:
		var error = json.parse(udp_peer.get_packet().get_string_from_utf8())
		if error == OK:
			var data = json.data
			if typeof(data) == TYPE_DICTIONARY:
				print(udp_peer.get_local_port()," Received: ", data)
				packet_received(data)
			else:
				print("Error parsing JSON, wring type: ", error)
		else:
			print("Error parsing JSON: ", error)


func _exit_tree() -> void:
	print("UDP is closing")
	if udp_peer.is_socket_connected():
		udp_peer.close()
		print("UDP connection closed")