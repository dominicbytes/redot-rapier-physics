extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	assert(await run(root), "Regression test did not complete")
	print("EXPECTED DIAGNOSTICS TEST: SUCCESS")
	quit(0)


func run(host: Node) -> bool:
	var world := Node2D.new()
	host.add_child(world)
	var body := RigidBody2D.new()
	body.name = "SavedBody"
	var shape := CollisionShape2D.new()
	shape.shape = CircleShape2D.new()
	body.add_child(shape)
	world.add_child(body)
	var manager = ClassDB.instantiate("StateManager2D")
	host.add_child(manager)
	manager.root_node = world
	for frame in 3:
		await host.get_tree().physics_frame
	var space := world.get_world_2d().space
	PhysicsServer2D.space_set_active(space, false)
	var serialized: String = manager.export_state(space, "Json")
	for count in [1, -1]:
		var malformed := serialized.replace('"contact_count":0', '"contact_count":%d' % count)
		assert(malformed != serialized)
		var transform := Transform2D(0.0, Vector2(120, 180))
		PhysicsServer2D.body_set_state(body.get_rid(), PhysicsServer2D.BODY_STATE_TRANSFORM, transform)
		var before: String = manager.export_state(space, "Json")
		manager.import_state(space, malformed)
		assert(manager.export_state(space, "Json") == before, "Malformed snapshot changed live state")
		var direct := PhysicsServer2D.body_get_direct_state(body.get_rid())
		assert(direct.get_contact_count() == 0)
		for index in [-1, 0, 1]:
			assert(direct.get_contact_local_position(index) == Vector2.ZERO)
			assert(RapierPhysicsServer2D.body_get_contact_tangent_impulse(body.get_rid(), index) == 0.0)
	PhysicsServer2D.space_set_active(space, true)
	manager.free()
	world.free()
	return true
