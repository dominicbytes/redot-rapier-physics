extends Node2D

func run() -> bool:
	var body := RigidBody2D.new()
	body.custom_integrator = true
	body.can_sleep = false
	var collision := CollisionShape2D.new()
	collision.shape = CircleShape2D.new()
	body.add_child(collision)
	add_child(body)
	for i in 4:
		await get_tree().physics_frame
	body.gravity_scale = 2.0
	for i in 8:
		await get_tree().physics_frame
	var passed := body.position.is_zero_approx() and body.linear_velocity.is_zero_approx()
	print("CUSTOM INTEGRATOR: ", body.position, " ", body.linear_velocity)
	body.queue_free()
	for i in 3:
		await get_tree().physics_frame
	return passed
