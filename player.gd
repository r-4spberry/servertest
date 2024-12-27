extends Node2D

var is_local: bool = false

signal send_data(packet)

func ready() -> void:
	$PlayerCharacter.is_local = is_local
	$PlayerCharacter.init()
	$PlayerCharacter.update_color()
	$PlayerCharacter.is_active = true