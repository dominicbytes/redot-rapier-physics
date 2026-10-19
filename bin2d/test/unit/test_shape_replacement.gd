extends RefCounted

func run(tree: SceneTree) -> void:
	for is_area in [false, true]:
		await _test_replacement(tree, is_area, false)
		await _test_replacement(tree, is_area, true)
	print("Shape replacement tests passed.")

func _test_replacement(tree: SceneTree, is_area: bool, disabled: bool) -> void:
	var world := Node2D.new()
	tree.root.add_child(world)
	var object: CollisionObject2D = Area2D.new() if is_area else StaticBody2D.new()
	var slot := CollisionShape2D.new()
	var small := CircleShape2D.new()
	small.radius = 5.0
	slot.shape = small
	slot.position = Vector2(1000, 1000)
	slot.disabled = disabled
	slot.one_way_collision = true
	slot.one_way_collision_margin = 3.0
	object.add_child(slot)
	world.add_child(object)
	var rid := object.get_rid()
	var original_transform := Transform2D(0.0, slot.position)
	var query := PhysicsShapeQueryParameters2D.new()
	var probe := CircleShape2D.new()
	probe.radius = 1.0
	query.shape = probe
	query.transform = Transform2D(0.0, slot.position + Vector2(30, 0))
	query.collide_with_bodies = not is_area
	query.collide_with_areas = is_area
	var state := world.get_world_2d().direct_space_state
	await _settle(tree)
	assert(state.intersect_shape(query).is_empty())
	var large := CircleShape2D.new()
	large.radius = 50.0
	if is_area:
		PhysicsServer2D.area_set_shape(rid, 0, large.get_rid())
		assert(PhysicsServer2D.area_get_shape_transform(rid, 0) == original_transform)
	else:
		PhysicsServer2D.body_set_shape(rid, 0, large.get_rid())
		assert(PhysicsServer2D.body_get_shape_transform(rid, 0) == original_transform)
	await _settle(tree)
	assert(state.intersect_shape(query).size() == (0 if disabled else 1), "Replacement must use the new geometry and preserve disabled state")
	if disabled:
		if is_area:
			PhysicsServer2D.area_set_shape_disabled(rid, 0, false)
		else:
			PhysicsServer2D.body_set_shape_disabled(rid, 0, false)
		await _settle(tree)
		assert(state.intersect_shape(query).size() == 1)
	query.transform.origin += Vector2(40, 0)
	assert(state.intersect_shape(query).is_empty())
	large.radius = 80.0
	await _settle(tree)
	assert(state.intersect_shape(query).size() == 1, "Changes to the new shape must notify its owner")
	large.radius = 5.0
	await _settle(tree)
	assert(state.intersect_shape(query).is_empty())
	small.radius = 100.0
	await _settle(tree)
	assert(state.intersect_shape(query).is_empty(), "The old shape must no longer own the slot")
	world.queue_free()
	await _settle(tree)

func _settle(tree: SceneTree) -> void:
	for frame in 3:
		await tree.physics_frame
