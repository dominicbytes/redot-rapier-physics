extends Node

var _clicks: Dictionary = {}

func _receive_input(_viewport: Node, event: InputEvent, _shape: int, label: String) -> void:
	if event is InputEventMouseButton and event.pressed:
		_clicks[label] += 1

func _settle() -> void:
	for frame in range(4):
		await get_tree().physics_frame
		await get_tree().process_frame

func run() -> bool:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(256, 256)
	viewport.world_2d = World2D.new()
	viewport.physics_object_picking = true
	viewport.handle_input_locally = true
	add_child(viewport)
	viewport.notify_mouse_entered()
	var objects: Array[CollisionObject2D] = []
	for area in [false, true]:
		for pickable in [false, true]:
			var object: CollisionObject2D = Area2D.new() if area else StaticBody2D.new()
			object.name = ("area" if area else "body") + ("_pickable" if pickable else "_nonpickable")
			object.input_pickable = pickable
			object.position = Vector2(128, 128)
			object.collision_mask = 0
			var collision := CollisionShape2D.new()
			var shape := CircleShape2D.new()
			shape.radius = 20
			collision.shape = shape
			object.add_child(collision)
			_clicks[object.name] = 0
			object.input_event.connect(_receive_input.bind(String(object.name)))
			viewport.add_child(object)
			objects.append(object)
	await _settle()
	var state := viewport.world_2d.direct_space_state
	var context_available := state.has_method("is_picking_query")
	var rapier := PhysicsServer2D.get_class() == "RapierPhysicsServer2D"
	var fallback: bool = ProjectSettings.get_setting("physics/rapier/queries/point_query_honors_pickable", true)
	var passed := true
	# Official engines lack the context method. Check their existing fallback
	# contract; require built-in parity only when the method is available.
	for round_index in range(2):
		if context_available:
			passed = passed and not bool(state.call("is_picking_query"))
		var query := PhysicsPointQueryParameters2D.new()
		query.position = Vector2(128, 128)
		query.collide_with_areas = true
		var hits := state.intersect_point(query, 16)
		var expected_hits := 2 if rapier and not context_available and fallback else 4
		passed = passed and hits.size() == expected_hits
		for object in objects:
			var found := 0
			for hit in hits:
				if hit.collider == object:
					found += 1
			var expected := 1 if object.input_pickable or not rapier or context_available or not fallback else 0
			passed = passed and found == expected
		var event := InputEventMouseButton.new()
		event.position = query.position
		event.global_position = query.position
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = true
		viewport.push_input(event, true)
		await _settle()
		for object in objects:
			var receives_input: bool = object.input_pickable or (rapier and not context_available and not fallback)
			var expected_clicks := round_index + 1 if receives_input else 0
			passed = passed and _clicks[object.name] == expected_clicks
			print("POINT PICKING ", object.name, " round=", round_index, " input=", _clicks[object.name], " expected=", expected_clicks)
		if context_available:
			passed = passed and not bool(state.call("is_picking_query"))
		print("POINT QUERY context=", context_available, " fallback=", fallback, " hits=", hits.size(), " expected=", expected_hits)
	viewport.queue_free()
	await get_tree().process_frame
	print("Point picking tests passed." if passed else "Point picking tests failed.")
	return passed
