extends RefCounted

func run(host: Node) -> bool:
	var world := Node2D.new()
	host.add_child(world)
	var body := RigidBody2D.new()
	body.name = "SavedBody"
	body.can_sleep = false
	var collision := CollisionShape2D.new()
	collision.shape = CircleShape2D.new()
	body.add_child(collision)
	world.add_child(body)
	var manager = ClassDB.instantiate("StateManager2D")
	host.add_child(manager)
	manager.root_node = world
	var rid := body.get_rid()
	var params := [PhysicsServer2D.BODY_PARAM_GRAVITY_SCALE, PhysicsServer2D.BODY_PARAM_LINEAR_DAMP_MODE, PhysicsServer2D.BODY_PARAM_ANGULAR_DAMP_MODE, PhysicsServer2D.BODY_PARAM_LINEAR_DAMP, PhysicsServer2D.BODY_PARAM_ANGULAR_DAMP]
	var saved := [1.0, PhysicsServer2D.BODY_DAMP_MODE_REPLACE, PhysicsServer2D.BODY_DAMP_MODE_REPLACE, 0.0, 0.0]
	for i in params.size():
		PhysicsServer2D.body_set_param(rid, params[i], saved[i])
	for frame in 4:
		await host.get_tree().physics_frame
	var space := world.get_world_2d().space
	PhysicsServer2D.space_set_active(space, false)
	manager.cache_state(space, "saved")
	var snapshots: Array = []
	for format in ["Json", "GodotBase64", "RustBincode"]:
		snapshots.append(manager.export_state(space, format))
	for snapshot in [null] + snapshots:
		for i in params.size():
			PhysicsServer2D.body_set_param(rid, params[i], [2.0, 0, 0, 5.0, 7.0][i])
		if snapshot == null:
			assert(manager.load_cached_state(space, 0))
		else:
			manager.import_state(space, snapshot)
		for i in params.size():
			assert(is_equal_approx(float(PhysicsServer2D.body_get_param(rid, params[i])), float(saved[i])), "Snapshot did not restore body parameter")
		var state := PhysicsServer2D.body_get_direct_state(rid)
		assert(is_zero_approx(state.total_linear_damp))
		assert(is_zero_approx(state.total_angular_damp))
		var saved_velocity := state.linear_velocity.y
		for frame in 6:
			RapierPhysicsServer2D.space_step(space, 1.0 / 60.0)
		assert(absf(state.linear_velocity.y - saved_velocity - 98.0) < 0.1, "Loaded simulation disagrees with saved gravity")
		# Repeat the post-save value: a stale wrapper would skip this setter.
		PhysicsServer2D.body_set_param(rid, PhysicsServer2D.BODY_PARAM_GRAVITY_SCALE, 2.0)
		var before := state.linear_velocity.y
		for frame in 6:
			RapierPhysicsServer2D.space_step(space, 1.0 / 60.0)
		var delta := state.linear_velocity.y - before
		assert(absf(delta - 196.0) < 0.1, "Restored trajectory disagrees with gravity getter")
	PhysicsServer2D.space_set_active(space, true)
	manager.free()
	world.free()
	return true
