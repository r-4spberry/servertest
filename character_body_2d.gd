extends CharacterBody2D

var is_local

var timer: Timer = Timer.new()

var last_movement: Dictionary;

var is_active = false;

var server_position;
var server_velocity;

var id = -1;

var speed = 300;

var parent;

@onready var particles = $CPUParticles2D

var actions = []

func capture_input(vellocity) -> void:
	last_movement = {
		"type": "move",
		"data":
			{
				"position": {
					"x": position.x,
					"y": position.y
				},
				"velocity": vellocity
			}
	}


func handle_input() -> void:
	var x = (Input.get_action_strength("ui_right") - Input.get_action_strength("ui_left"))
	var y = (Input.get_action_strength("ui_down") - Input.get_action_strength("ui_up"))

	if x != 0 or y != 0:
		capture_input({"x": x, "y": y})
	
	velocity = Vector2(x, y) * speed

func init() -> void:
	if is_local:
		timer.wait_time = 0.03
		timer.autostart = true
		timer.connect("timeout", Callable(self, "send_data"))
		add_child(timer)

func get_server_time():
	return Time.get_ticks_msec()

func handle_response(data: Dictionary) -> void:
	print("handling ", data)
	if data["type"] == "move":
		if is_local:
			return
		else:
			var pos = data["data"]["position"]
			server_position = Vector2(pos["x"], pos["y"])
			var vel = data["data"]["velocity"]
			server_velocity = Vector2(vel["x"], vel["y"])
	if data["type"] == "action":
		print(data)
		if is_local:
			return
		print(data["data"]["data"]["type"])
		if data["data"]["data"]["type"] == "emit_particles":
			emit_particles()
func send_data() -> void:
	if not is_active:
		return

	var packet = {
		"id": id,
		"type": "actions",
		"timestamp": get_server_time(),
		"actions": []
	}
	if last_movement != {}:
		packet["actions"].append(last_movement)
	last_movement = {}

	for action in actions:
		packet["actions"].append(action)

	actions = []

	if len(packet["actions"]) == 0:
		return

	parent.send_data.emit(packet)
	packet["timestamp"] += 1


func update_color() -> void:
	$PlayerSprite.modulate = Color(1, 1, 1) if is_local else Color(0.5, 0.5, 1)

func sync_with_server() -> void:
	#lerp
	if server_position == null:
		return
	position = lerp(position, server_position, 0.5)
	
	pass

func _physics_process(_delta: float) -> void:
	if not is_active:
		return
	
	if is_local:
		handle_input()
		move_and_slide()
	else:
		sync_with_server()
		
func _process(_delta):
	if not is_active or not is_local:
		return

	if Input.is_action_just_pressed("ui_accept"):  # Spacebar is the default "ui_accept"
		emit_particles()

func emit_particles():
	if particles.emitting == false:
		particles.emitting = true  # Start emitting particles
		if is_local:
			actions.append({
				"type": "action",
				"data": {"type": "emit_particles"}
			})

func _ready() -> void:
	parent = get_parent()