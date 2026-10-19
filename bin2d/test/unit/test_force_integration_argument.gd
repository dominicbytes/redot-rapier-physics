extends Node2D

var called: Array[bool] = [false, false, false, false]

func run() -> bool:
	var bodies: Array[RID] = []
	var shape := PhysicsServer2D.circle_shape_create()
	PhysicsServer2D.shape_set_data(shape, 5.0)
	for i in 4:
		var body := PhysicsServer2D.body_create()
		bodies.append(body)
		PhysicsServer2D.body_set_mode(body, PhysicsServer2D.BODY_MODE_RIGID)
		PhysicsServer2D.body_add_shape(body, shape)
		PhysicsServer2D.body_set_state(body, PhysicsServer2D.BODY_STATE_TRANSFORM, Transform2D(0, Vector2(i * 30, 0)))
		PhysicsServer2D.body_set_space(body, get_world_2d().space)
		PhysicsServer2D.body_set_state(body, PhysicsServer2D.BODY_STATE_CAN_SLEEP, false)
		if i >= 2:
			assert(PhysicsServer2D.body_get_direct_state(body) != null)
		if i % 2 == 0:
			PhysicsServer2D.body_set_force_integration_callback(body, receive_state.bind(i))
		else:
			PhysicsServer2D.body_set_force_integration_callback(body, receive_userdata.bind(i), {"body": body, "value": 42})
	for i in 8:
		await get_tree().physics_frame
	print("FORCE INTEGRATION ARGUMENTS: ", called)
	var passed := not called.has(false)
	for body in bodies:
		PhysicsServer2D.body_set_force_integration_callback(body, Callable())
		PhysicsServer2D.free_rid(body)
	PhysicsServer2D.free_rid(shape)
	await get_tree().physics_frame
	return passed

func receive_state(state: PhysicsDirectBodyState2D, index: int) -> void:
	called[index] = state != null

func receive_userdata(state: PhysicsDirectBodyState2D, userdata: Dictionary, index: int) -> void:
	called[index] = state != null and userdata.value == 42 and state == PhysicsServer2D.body_get_direct_state(userdata.body)
