extends Node2D

var passed: bool = true

func run() -> bool:
	var area := Area2D.new()
	area.gravity_space_override = Area2D.SPACE_OVERRIDE_REPLACE
	area.gravity = 100.0
	area.linear_damp_space_override = Area2D.SPACE_OVERRIDE_REPLACE
	area.linear_damp = 2.0
	area.angular_damp_space_override = Area2D.SPACE_OVERRIDE_REPLACE
	area.angular_damp = 3.0
	var area_collision := CollisionShape2D.new()
	var rectangle := RectangleShape2D.new()
	rectangle.size = Vector2(2000, 2000)
	area_collision.shape = rectangle
	area.add_child(area_collision)
	add_child(area)
	var body := RigidBody2D.new()
	body.custom_integrator = true
	body.can_sleep = false
	var collision := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = 5.0
	collision.shape = circle
	body.add_child(collision)
	add_child(body)
	await wait_frames(8)
	check_totals(body, 100.0, 2.0, 3.0)
	body.gravity_scale = 0.0
	body.linear_damp = 5.0
	body.angular_damp = 7.0
	await wait_frames(3)
	check_totals(body, 0.0, 7.0, 10.0)
	body.linear_damp_mode = RigidBody2D.DAMP_MODE_REPLACE
	body.angular_damp_mode = RigidBody2D.DAMP_MODE_REPLACE
	await wait_frames(3)
	check_totals(body, 0.0, 5.0, 7.0)
	body.linear_damp_mode = RigidBody2D.DAMP_MODE_COMBINE
	body.angular_damp_mode = RigidBody2D.DAMP_MODE_COMBINE
	body.gravity_scale = 2.0
	await wait_frames(3)
	check_totals(body, 200.0, 7.0, 10.0)
	area.queue_free()
	body.queue_free()
	await wait_frames(3)
	return passed

func wait_frames(count: int) -> void:
	for i in count:
		await get_tree().physics_frame

func check_totals(body: RigidBody2D, gravity: float, linear: float, angular: float) -> void:
	var state := PhysicsServer2D.body_get_direct_state(body.get_rid())
	print("AREA TOTALS: ", state.total_gravity, " ", state.total_linear_damp, " ", state.total_angular_damp)
	passed = state.total_gravity.is_equal_approx(Vector2(0, gravity)) and passed
	passed = is_equal_approx(state.total_linear_damp, linear) and passed
	passed = is_equal_approx(state.total_angular_damp, angular) and passed
