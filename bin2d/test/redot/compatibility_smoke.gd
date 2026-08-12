extends Node2D

const EXPECTED_BACKEND := "Rapier2D"


func _ready() -> void:
	call_deferred("_run_smoke")


func _fail(message: String) -> void:
	push_error(message)
	get_tree().quit(1)


func _run_smoke() -> void:
	var backend := str(ProjectSettings.get_setting("physics/2d/physics_engine", ""))
	if backend != EXPECTED_BACKEND:
		_fail("Expected Rapier2D backend, got %s" % backend)
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
		body.queue_free()
		await get_tree().process_frame
		_fail("Rapier2D direct-space point query returned no collision")
		return

	body.queue_free()
	await get_tree().process_frame
	print("REDOT RAPIER2D COMPATIBILITY SMOKE: SUCCESS")
	get_tree().quit(0)
