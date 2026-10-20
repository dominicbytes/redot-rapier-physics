extends RefCounted

var passed := true

func run(host: Node) -> bool:
	var cases := [
		[WorldBoundaryShape2D.new(), [Vector2(0, -2), -5.0], [Vector2.RIGHT, 40.0]],
		[CircleShape2D.new(), 10.0, 30.0],
		[RectangleShape2D.new(), Vector2(10, 10), Vector2(30, 30)],
		[CapsuleShape2D.new(), Vector2(30, 5), Vector2(60, 10)],
		[SegmentShape2D.new(), Rect2(-20, 10, 40, 0), Rect2(-20, 30, 40, 0)],
		[ConvexPolygonShape2D.new(), PackedVector2Array([Vector2(-10, -10), Vector2(10, -10), Vector2(10, 10), Vector2(-10, 10)]), PackedVector2Array([Vector2(-30, -30), Vector2(30, -30), Vector2(30, 30), Vector2(-30, 30)])],
		[ConcavePolygonShape2D.new(), PackedVector2Array([Vector2(-20, 10), Vector2(20, 10)]), PackedVector2Array([Vector2(-20, 30), Vector2(20, 30)])],
	]
	for data in cases:
		await check_shape(host, data[0], data[1], data[2])
	await check_ray(host)
	return passed

func check_shape(host: Node, shape: Shape2D, saved, changed) -> void:
	var world := Node2D.new()
	host.add_child(world)
	var body := StaticBody2D.new()
	body.name = "SavedShape"
	var collision := CollisionShape2D.new()
	collision.shape = shape
	body.add_child(collision)
	world.add_child(body)
	var rid := shape.get_rid()
	PhysicsServer2D.shape_set_data(rid, saved)
	for frame in 2:
		await host.get_tree().physics_frame
	var space := world.get_world_2d().space
	PhysicsServer2D.space_set_active(space, false)
	var original = PhysicsServer2D.shape_get_data(rid)
	var hit := ray_hit(space)
	assert(not hit.is_empty(), "Saved geometry must intersect the probe ray")
	var manager = ClassDB.instantiate("StateManager2D")
	host.add_child(manager)
	manager.root_node = world
	manager.cache_state(space, "saved")
	var snapshots: Array = [null]
	for format in ["Json", "GodotBase64", "RustBincode"]:
		snapshots.append(manager.export_state(space, format))
	snapshots.append(manager.export_state_from_cache(0, "RustBincode"))
	# Ordinary shapes leave the new parameter map empty (8 bytes in bincode).
	# Keep JSON text intact so integer fields do not become floats on re-encoding.
	if not shape is WorldBoundaryShape2D and JSON.parse_string(snapshots[1]).has("shape_parameters"):
		var binary: PackedByteArray = snapshots[3]
		snapshots.append(binary.slice(0, binary.size() - 8))
		var legacy: String = snapshots[1]
		assert(legacy.ends_with(',"shape_parameters":{}}'))
		legacy = legacy.trim_suffix(',"shape_parameters":{}}') + "}"
		snapshots.append(legacy)
		legacy = legacy.substr(0, legacy.rfind(',"body_parameters":')) + "}"
		snapshots.append(Marshalls.utf8_to_base64(legacy))
	# Halfspaces have a non-finite Rapier body extent in JSON; exercise their
	# cache/binary formats here. Separation rays use a custom unserializable shape.
	for snapshot in ([snapshots[0], snapshots[3], snapshots[4]] if shape is WorldBoundaryShape2D else snapshots):
		PhysicsServer2D.shape_set_data(rid, changed)
		if snapshot == null:
			assert(manager.load_cached_state(space, 0))
		else:
			manager.import_state(space, snapshot)
		var restored = PhysicsServer2D.shape_get_data(rid)
		var restored_hit := ray_hit(space)
		var data_ok: bool = restored == original
		var geometry_ok: bool = not restored_hit.is_empty() and restored_hit.position.is_equal_approx(hit.position) and restored_hit.normal.is_equal_approx(hit.normal)
		print("SNAPSHOT ", shape.get_class(), " data=", restored, " expected=", original, " geometry=", geometry_ok)
		passed = data_ok and geometry_ok and passed
	PhysicsServer2D.space_set_active(space, true)
	manager.free()
	world.free()

func ray_hit(space: RID) -> Dictionary:
	var query := PhysicsRayQueryParameters2D.create(Vector2(0, -100), Vector2(0, 100))
	return PhysicsServer2D.space_get_direct_state(space).intersect_ray(query)

func check_ray(host: Node) -> void:
	var world := Node2D.new()
	host.add_child(world)
	var floor_body := StaticBody2D.new()
	floor_body.position.y = 40.0
	var floor_collision := CollisionShape2D.new()
	var floor_shape := RectangleShape2D.new()
	floor_shape.size = Vector2(200, 2)
	floor_collision.shape = floor_shape
	floor_body.add_child(floor_collision)
	world.add_child(floor_body)
	var body := CharacterBody2D.new()
	body.name = "SavedRay"
	var collision := CollisionShape2D.new()
	var ray := SeparationRayShape2D.new()
	collision.shape = ray
	body.add_child(collision)
	world.add_child(body)
	var rid := ray.get_rid()
	var saved := {"length": 30.0, "slide_on_slope": false}
	PhysicsServer2D.shape_set_data(rid, saved)
	for frame in 2:
		await host.get_tree().physics_frame
	var space := world.get_world_2d().space
	PhysicsServer2D.space_set_active(space, false)
	var manager = ClassDB.instantiate("StateManager2D")
	host.add_child(manager)
	manager.root_node = world
	var motion := PhysicsTestMotionParameters2D.new()
	motion.motion = Vector2(0, 20)
	var before := PhysicsTestMotionResult2D.new()
	var saved_collision := PhysicsServer2D.body_test_motion(body.get_rid(), motion, before)
	manager.cache_state(space, "ray")
	PhysicsServer2D.shape_set_data(rid, {"length": 5.0, "slide_on_slope": true})
	assert(manager.load_cached_state(space, 0))
	var after := PhysicsTestMotionResult2D.new()
	var restored_collision := PhysicsServer2D.body_test_motion(body.get_rid(), motion, after)
	var data_ok: bool = PhysicsServer2D.shape_get_data(rid) == saved
	var motion_ok: bool = saved_collision == restored_collision and before.get_travel().is_equal_approx(after.get_travel())
	print("SNAPSHOT SeparationRayShape2D data=", data_ok, " motion=", motion_ok, " before=", before.get_travel(), " after=", after.get_travel())
	passed = data_ok and motion_ok and passed
	PhysicsServer2D.space_set_active(space, true)
	manager.free()
	world.free()
