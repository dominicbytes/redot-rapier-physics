extends Node2D

func counts(state: PhysicsDirectSpaceState2D, shape: Shape2D, position: Vector2) -> Vector2i:
	var point := PhysicsPointQueryParameters2D.new()
	point.position = position
	var query := PhysicsShapeQueryParameters2D.new()
	query.shape = shape
	query.transform = Transform2D(0, position)
	return Vector2i(state.intersect_point(point).size(), state.intersect_shape(query).size())

func _ready():
	var passed := true
	for mode in [PhysicsServer2D.BODY_MODE_STATIC, PhysicsServer2D.BODY_MODE_KINEMATIC]:
		var space := PhysicsServer2D.space_create()
		var shape := CircleShape2D.new()
		shape.radius = 2.0
		var probe := CircleShape2D.new()
		probe.radius = 0.5
		var body := PhysicsServer2D.body_create()
		PhysicsServer2D.body_set_mode(body, PhysicsServer2D.BODY_MODE_STATIC)
		PhysicsServer2D.body_add_shape(body, shape.get_rid(), Transform2D(0, Vector2(0, 4)))
		PhysicsServer2D.body_add_shape(body, shape.get_rid(), Transform2D(0, Vector2(0, -4)))
		PhysicsServer2D.body_set_state(body, PhysicsServer2D.BODY_STATE_TRANSFORM, Transform2D(0, Vector2(10, 0)))
		PhysicsServer2D.body_set_space(body, space)
		PhysicsServer2D.body_set_mode(body, mode)
		if PhysicsServer2D.get_class() == "RapierPhysicsServer2D":
			RapierPhysicsServer2D.space_step(space, 1.0 / 60.0)
		var state := PhysicsServer2D.space_get_direct_state(space)
		for offset in [Vector2(0, 4), Vector2(0, -4)]:
			passed = passed and counts(state, probe, Vector2(10, 0) + offset) == Vector2i.ONE
		PhysicsServer2D.body_set_state(body, PhysicsServer2D.BODY_STATE_TRANSFORM, Transform2D(PI / 2, Vector2(30, 0)))
		var old_now := counts(state, probe, Vector2(10, 4))
		var first_now := counts(state, probe, Vector2(26, 0))
		print("POSE FIRST mode=", mode, " old=", old_now, " new=", first_now)
		passed = passed and old_now == Vector2i.ZERO and first_now == Vector2i.ONE
		PhysicsServer2D.body_set_state(body, PhysicsServer2D.BODY_STATE_TRANSFORM, Transform2D(PI / 2, Vector2(50, 0)))
		var deferred: bool = mode == PhysicsServer2D.BODY_MODE_KINEMATIC
		var first_again := counts(state, probe, Vector2(26, 0))
		var second_now := counts(state, probe, Vector2(46, 0))
		print("POSE SECOND mode=", mode, " old=", first_again, " new=", second_now)
		passed = passed and first_again == (Vector2i.ONE if deferred else Vector2i.ZERO)
		passed = passed and second_now == (Vector2i.ZERO if deferred else Vector2i.ONE)
		if PhysicsServer2D.get_class() == "RapierPhysicsServer2D":
			RapierPhysicsServer2D.space_step(space, 1.0 / 60.0)
			passed = passed and counts(state, probe, Vector2(26, 0)) == Vector2i.ZERO
			passed = passed and counts(state, probe, Vector2(46, 0)) == Vector2i.ONE
			if deferred:
				var velocity: Vector2 = PhysicsServer2D.body_get_state(body, PhysicsServer2D.BODY_STATE_LINEAR_VELOCITY)
				print("POSE PLATFORM velocity=", velocity)
				passed = passed and velocity.is_equal_approx(Vector2(1200, 0))
		if not deferred:
			var scaled := Transform2D(0, Vector2(70, 0)).scaled_local(Vector2(2, 2))
			PhysicsServer2D.body_set_state(body, PhysicsServer2D.BODY_STATE_TRANSFORM, scaled)
			var scaled_now := counts(state, probe, Vector2(73, 8))
			print("POSE SCALED new=", scaled_now)
			passed = passed and scaled_now == Vector2i.ONE
		PhysicsServer2D.free_rid(body)
		PhysicsServer2D.free_rid(space)
	assert(passed, "Queries must see static and first kinematic poses immediately, and later targets after stepping")
	print("Query pose tests passed.")
