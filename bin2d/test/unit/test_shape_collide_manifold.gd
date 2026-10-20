extends RefCounted


func run() -> void:
	var rect := RectangleShape2D.new()
	rect.size = Vector2(10, 10)
	var circle := CircleShape2D.new()
	circle.radius = 5.0
	var capsule := CapsuleShape2D.new()
	capsule.radius = 3.0
	capsule.height = 14.0
	var convex := ConvexPolygonShape2D.new()
	convex.points = PackedVector2Array([
		Vector2(-5, -5), Vector2(5, -5), Vector2(5, 5), Vector2(-5, 5),
	])
	var triangle := ConvexPolygonShape2D.new()
	triangle.points = PackedVector2Array([Vector2(-5, -5), Vector2(5, -5), Vector2(0, 5)])
	_check_pair(rect, rect, Vector2(5, 0), PackedVector2Array([
		Vector2(5, -5), Vector2(0, -5), Vector2(5, 5), Vector2(0, 5),
	]))
	_check_pair(circle, rect, Vector2(7, 0), PackedVector2Array([
		Vector2(5, 0), Vector2(2, 0),
	]))
	_check_pair(capsule, rect, Vector2(7, 0), PackedVector2Array([
		Vector2(3, -4), Vector2(2, -4), Vector2(3, 4), Vector2(2, 4),
	]))
	_check_pair(convex, rect, Vector2(5, 0), PackedVector2Array([
		Vector2(5, -5), Vector2(0, -5), Vector2(5, 5), Vector2(0, 5),
	]))
	_check_pair(triangle, rect, Vector2(0, 7), PackedVector2Array([
		Vector2(0, 5), Vector2(0, 2),
	]))
	var a := Transform2D(0, Vector2(30, 40))
	var b := Transform2D(0, Vector2(50, 40))
	for motions in [[Vector2(14, 0), Vector2.ZERO], [Vector2.ZERO, Vector2(-14, 0)],
			[Vector2(7, 0), Vector2(-7, 0)]]:
		var contacts := rect.collide_with_motion_and_get_contacts(a, motions[0], rect, b, motions[1])
		assert(contacts.size() == 4, "Moving rectangles must report both edge contacts")
		for point in contacts:
			assert(point.is_finite())
		assert(is_equal_approx(contacts[0].y, contacts[1].y))
		assert(is_equal_approx(contacts[2].y, contacts[3].y))
		assert(not is_equal_approx(contacts[0].y, contacts[2].y))
	assert(rect.collide_with_motion_and_get_contacts(a, Vector2(-14, 0), rect, b, Vector2.ZERO).is_empty())
	_check_space_limit(rect)
	print("Shape collide manifold tests passed.")


func _check_pair(a: Shape2D, b: Shape2D, offset: Vector2, expected: PackedVector2Array) -> void:
	# Compare whole pairs: endpoints must remain A then B, while pair order is unspecified.
	var origin := Vector2(30, 40)
	var pose_a := Transform2D(0, origin)
	var pose_b := Transform2D(0, origin + offset)
	for swapped in [false, true]:
		var contacts := b.collide_and_get_contacts(pose_b, a, pose_a) if swapped else a.collide_and_get_contacts(pose_a, b, pose_b)
		assert(contacts.size() == expected.size(), "Every manifold contact must be returned")
		for i in range(0, expected.size(), 2):
			var first := expected[i + 1 if swapped else i] + origin
			var second := expected[i if swapped else i + 1] + origin
			var found := false
			for j in range(0, contacts.size(), 2):
				if contacts[j].distance_to(first) < 0.01 and contacts[j + 1].distance_to(second) < 0.01:
					found = true
			assert(found, "Contact pairs must contain world points on A then B")


func _check_space_limit(shape: Shape2D) -> void:
	var space := PhysicsServer2D.space_create()
	var body := PhysicsServer2D.body_create()
	PhysicsServer2D.body_set_mode(body, PhysicsServer2D.BODY_MODE_STATIC)
	PhysicsServer2D.body_add_shape(body, shape.get_rid())
	PhysicsServer2D.body_set_state(body, PhysicsServer2D.BODY_STATE_TRANSFORM, Transform2D(0, Vector2(5, 0)))
	PhysicsServer2D.body_set_space(body, space)
	var query := PhysicsShapeQueryParameters2D.new()
	query.shape = shape
	var state := PhysicsServer2D.space_get_direct_state(space)
	for limit in [1, 2, 3, 8]:
		var contacts := state.collide_shape(query, limit)
		assert(contacts.size() == 2 * mini(limit, 2), "Limits count pairs, not individual points")
		for i in range(0, contacts.size(), 2):
			assert(absf(contacts[i].x - 5.0) < 0.01)
			assert(absf(contacts[i + 1].x) < 0.01)
	PhysicsServer2D.free_rid(body)
	PhysicsServer2D.free_rid(space)
