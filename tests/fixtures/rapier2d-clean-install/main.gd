extends Node2D

const RAPIER_BACKEND := "Rapier2D"
const DEFAULT_BACKEND := "DEFAULT"


func _ready() -> void:
	call_deferred("_run_checks")


func _fail(message: String) -> void:
	_write_result("FAIL", message)
	push_error(message)
	get_tree().quit(1)


func _result_path() -> String:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--rapier-result="):
			return argument.trim_prefix("--rapier-result=")
	return ""


func _write_result(status: String, message: String) -> void:
	var path := _result_path()
	if path.is_empty():
		return
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("Could not write clean-install result to %s" % path)
		return
	file.store_string(JSON.stringify({
		"status": status,
		"message": message,
		"selected_backend": ProjectSettings.get_setting(
			"physics/2d/physics_engine", DEFAULT_BACKEND
		),
		"rapier_server_registered": ClassDB.class_exists("RapierPhysicsServer2D"),
		"fluid_registered": ClassDB.class_exists("Fluid2D"),
		"state_manager_registered": ClassDB.class_exists("StateManager2D"),
	}) + "\n")


func _run_checks() -> void:
	var expected := str(ProjectSettings.get_setting("test/expected_backend", ""))
	var selected := str(ProjectSettings.get_setting(
		"physics/2d/physics_engine", DEFAULT_BACKEND
	))
	if selected != expected:
		_fail("Expected selected backend %s, got %s" % [expected, selected])
		return

	for class_name_value in ["RapierPhysicsServer2D", "Fluid2D", "StateManager2D"]:
		if not ClassDB.class_exists(class_name_value):
			_fail("Required packaged class is missing: %s" % class_name_value)
			return

	var body := StaticBody2D.new()
	body.input_pickable = true
	var collision_shape := CollisionShape2D.new()
	var rectangle := RectangleShape2D.new()
	rectangle.size = Vector2(64.0, 64.0)
	collision_shape.shape = rectangle
	body.add_child(collision_shape)
	add_child(body)

	await get_tree().physics_frame
	await get_tree().physics_frame

	var query := PhysicsPointQueryParameters2D.new()
	query.position = Vector2.ZERO
	query.collide_with_bodies = true
	query.collide_with_areas = false
	var hits := get_world_2d().direct_space_state.intersect_point(query, 8)
	if hits.is_empty():
		_fail("Packaged backend query returned no collision")
		return

	body.queue_free()
	await get_tree().process_frame
	_write_result("PASS", "clean install verified")
	if selected == RAPIER_BACKEND:
		print("REDOT RAPIER2D CLEAN INSTALL: SUCCESS")
	else:
		print("REDOT RAPIER2D DEFAULT CONTROL: SUCCESS")
	get_tree().quit(0)
