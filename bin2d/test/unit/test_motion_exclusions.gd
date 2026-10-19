extends Node2D

func _ready():
	var space := PhysicsServer2D.space_create()
	var circle := PhysicsServer2D.circle_shape_create()
	PhysicsServer2D.shape_set_data(circle, 1.0)
	var rectangle := PhysicsServer2D.rectangle_shape_create()
	PhysicsServer2D.shape_set_data(rectangle, Vector2(1, 10))
	var body := PhysicsServer2D.body_create()
	PhysicsServer2D.body_set_mode(body, PhysicsServer2D.BODY_MODE_KINEMATIC)
	PhysicsServer2D.body_add_shape(body, circle)
	PhysicsServer2D.body_set_space(body, space)
	var wall := PhysicsServer2D.body_create()
	PhysicsServer2D.body_set_mode(wall, PhysicsServer2D.BODY_MODE_STATIC)
	PhysicsServer2D.body_attach_object_instance_id(wall, get_instance_id())
	PhysicsServer2D.body_add_shape(wall, rectangle)
	PhysicsServer2D.body_set_state(wall, PhysicsServer2D.BODY_STATE_TRANSFORM, Transform2D(0, Vector2(10, 0)))
	PhysicsServer2D.body_set_space(wall, space)
	if PhysicsServer2D.get_class() == "RapierPhysicsServer2D":
		RapierPhysicsServer2D.space_step(space, 1.0 / 60.0)
	var parameters := PhysicsTestMotionParameters2D.new()
	parameters.motion = Vector2(10, 0)
	var result := PhysicsTestMotionResult2D.new()
	assert(PhysicsServer2D.body_test_motion(body, parameters, result))
	var passed := true
	for object_exclusion in [false, true]:
		parameters.exclude_bodies = [] if object_exclusion else [wall]
		parameters.exclude_objects = [get_instance_id()] if object_exclusion else []
		for recovery in [false, true]:
			parameters.from = Transform2D(0, Vector2(8.5, 0)) if recovery else Transform2D.IDENTITY
			parameters.motion = Vector2(0, 1) if recovery else Vector2(10, 0)
			parameters.recovery_as_collision = recovery
			var collided := PhysicsServer2D.body_test_motion(body, parameters, result)
			var unchanged := result.get_travel().is_equal_approx(parameters.motion)
			print("MOTION EXCLUSION object=", object_exclusion, " recovery=", recovery, " collided=", collided, " travel=", result.get_travel())
			passed = passed and not collided and unchanged
	parameters.exclude_bodies = []
	parameters.exclude_objects = []
	parameters.from = Transform2D.IDENTITY
	parameters.motion = Vector2(10, 0)
	parameters.recovery_as_collision = false
	assert(PhysicsServer2D.body_test_motion(body, parameters, result))
	var query := PhysicsPointQueryParameters2D.new()
	query.position = Vector2(10, 0)
	var state := PhysicsServer2D.space_get_direct_state(space)
	assert(state.intersect_point(query).size() == 1)
	query.exclude = [wall]
	assert(state.intersect_point(query).is_empty())
	for rid in [body, wall, circle, rectangle, space]:
		PhysicsServer2D.free_rid(rid)
	assert(passed, "Motion exclusions must apply to both sweep and recovery")
	print("Motion exclusion tests passed.")
