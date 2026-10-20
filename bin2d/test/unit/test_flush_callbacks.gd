extends Node2D

# Area signals, area monitor callbacks and body state sync callbacks run while the physics
# server flushes its queries. Godot's built-in server lets them create, activate and free
# spaces and bodies, so these must work without crashing here as well.
#
# These tests need physics frames. The child scene waits for completion and reports
# assertion failures or a bounded completion error to the unit-test wrapper.

signal finished

# Enough new spaces to grow the server's space tables several times while they are in use.
const SPACE_COUNT := 20
# A layer no other unit test uses, so these objects only see each other.
const TEST_LAYER := 1 << 19
const TEST_ORIGIN := Vector2(-5000, -5000)

var done := false


func _ready():
	add_to_group(&"async_unit_tests")
	await test_free_space_detaches_objects()
	await test_area_signal_creates_spaces()
	await test_state_sync_creates_spaces_and_frees_body()
	await test_monitor_callback_frees_space()
	await test_state_sync_frees_space_with_pending_monitors()
	if ClassDB.class_exists(&"RapierPhysicsServer2D"):
		test_free_space_detaches_fluid()
	print("Flush callback tests passed.")
	done = true
	finished.emit()


func wait_physics_frames(count: int) -> void:
	for i in count:
		await get_tree().physics_frame


func new_collision_shape(shape: Shape2D) -> CollisionShape2D:
	var collision_shape := CollisionShape2D.new()
	collision_shape.shape = shape
	return collision_shape


# An Area2D body_entered handler that adds SubViewports holding physics bodies. Each
# SubViewport has its own World2D, which creates and activates a space when the first
# physics body enters it, so new spaces are created during the flush. The bodies have no
# shapes because the built-in server rejects shape changes while flushing queries.
func test_area_signal_creates_spaces():
	print("test_area_signal_creates_spaces")
	var area := Area2D.new()
	area.collision_layer = 0
	area.collision_mask = TEST_LAYER
	area.position = TEST_ORIGIN
	var area_rectangle := RectangleShape2D.new()
	area_rectangle.size = Vector2(40, 40)
	area.add_child(new_collision_shape(area_rectangle))

	var body := RigidBody2D.new()
	body.gravity_scale = 0.0
	body.collision_layer = TEST_LAYER
	body.collision_mask = 0
	body.position = TEST_ORIGIN
	body.add_child(new_collision_shape(CircleShape2D.new()))

	var viewports: Array[SubViewport] = []
	area.body_entered.connect(func(_entered: Node2D):
		for i in SPACE_COUNT:
			var viewport := SubViewport.new()
			viewport.add_child(StaticBody2D.new())
			add_child(viewport)
			viewports.append(viewport))
	add_child(area)
	add_child(body)

	await wait_physics_frames(5)
	assert(viewports.size() == SPACE_COUNT)
	for viewport in viewports:
		var space := viewport.world_2d.space
		assert(space.is_valid())
		assert(PhysicsServer2D.space_is_active(space))
	assert(area.overlaps_body(body))

	for viewport in viewports:
		viewport.queue_free()
	area.queue_free()
	body.queue_free()
	await wait_physics_frames(1)


# A body state sync callback that creates active spaces holding bodies, then frees the body
# it was called for.
func test_state_sync_creates_spaces_and_frees_body():
	print("test_state_sync_creates_spaces_and_frees_body")
	var space := PhysicsServer2D.space_create()
	PhysicsServer2D.space_set_active(space, true)
	var shape := PhysicsServer2D.circle_shape_create()
	PhysicsServer2D.shape_set_data(shape, 4.0)
	var body := PhysicsServer2D.body_create()
	PhysicsServer2D.body_set_mode(body, PhysicsServer2D.BODY_MODE_RIGID)
	PhysicsServer2D.body_add_shape(body, shape)
	PhysicsServer2D.body_set_collision_layer(body, 0)
	PhysicsServer2D.body_set_collision_mask(body, 0)
	PhysicsServer2D.body_set_space(body, space)

	var created: Array[RID] = []
	var calls := [0]
	var state_sync := func(_state: PhysicsDirectBodyState2D):
		calls[0] += 1
		for i in SPACE_COUNT:
			var new_space := PhysicsServer2D.space_create()
			PhysicsServer2D.space_set_active(new_space, true)
			var new_body := PhysicsServer2D.body_create()
			PhysicsServer2D.body_set_space(new_body, new_space)
			created.append_array([new_body, new_space])
		PhysicsServer2D.free_rid(body)
	PhysicsServer2D.body_set_state_sync_callback(body, state_sync)

	await wait_physics_frames(5)
	assert(calls[0] == 1)
	assert(created.size() == SPACE_COUNT * 2)
	for i in range(0, created.size(), 2):
		assert(PhysicsServer2D.body_get_space(created[i]) == created[i + 1])
		assert(PhysicsServer2D.space_is_active(created[i + 1]))

	for rid in created:
		PhysicsServer2D.free_rid(rid)
	PhysicsServer2D.free_rid(shape)
	PhysicsServer2D.free_rid(space)


# An area monitor callback that frees the space whose queries are being flushed.
func test_monitor_callback_frees_space():
	print("test_monitor_callback_frees_space")
	var space := PhysicsServer2D.space_create()
	PhysicsServer2D.space_set_active(space, true)
	var shape := PhysicsServer2D.circle_shape_create()
	PhysicsServer2D.shape_set_data(shape, 10.0)
	var area := PhysicsServer2D.area_create()
	PhysicsServer2D.area_add_shape(area, shape)
	PhysicsServer2D.area_set_collision_layer(area, 0)
	PhysicsServer2D.area_set_collision_mask(area, 1)
	PhysicsServer2D.area_set_space(area, space)
	var body := PhysicsServer2D.body_create()
	PhysicsServer2D.body_set_mode(body, PhysicsServer2D.BODY_MODE_KINEMATIC)
	PhysicsServer2D.body_add_shape(body, shape)
	PhysicsServer2D.body_set_collision_layer(body, 1)
	PhysicsServer2D.body_set_collision_mask(body, 0)
	PhysicsServer2D.body_set_space(body, space)

	var events: Array[int] = []
	var monitor := func(status: int, _body: RID, _instance: int, _body_shape: int, _area_shape: int):
		events.append(status)
		PhysicsServer2D.free_rid(space)
	PhysicsServer2D.area_set_monitor_callback(area, monitor)

	await wait_physics_frames(5)
	assert(events == [PhysicsServer2D.AREA_BODY_ADDED])
	assert(PhysicsServer2D.area_get_space(area) == RID())
	assert(PhysicsServer2D.body_get_space(body) == RID())

	PhysicsServer2D.free_rid(area)
	PhysicsServer2D.free_rid(body)
	PhysicsServer2D.free_rid(shape)


func test_free_space_detaches_objects() -> void:
	print("test_free_space_detaches_objects")
	var space := PhysicsServer2D.space_create()
	var next_space := PhysicsServer2D.space_create()
	var shape := PhysicsServer2D.circle_shape_create()
	PhysicsServer2D.shape_set_data(shape, 4.0)
	var bodies: Array[RID] = []
	for mode in [PhysicsServer2D.BODY_MODE_STATIC, PhysicsServer2D.BODY_MODE_KINEMATIC,
			PhysicsServer2D.BODY_MODE_RIGID, PhysicsServer2D.BODY_MODE_RIGID_LINEAR]:
		var body := PhysicsServer2D.body_create()
		PhysicsServer2D.body_set_mode(body, mode)
		PhysicsServer2D.body_add_shape(body, shape)
		PhysicsServer2D.body_set_state(body, PhysicsServer2D.BODY_STATE_TRANSFORM,
			Transform2D(0, Vector2(bodies.size() * 20, 0)))
		PhysicsServer2D.body_set_space(body, space)
		bodies.append(body)
	var area := PhysicsServer2D.area_create()
	PhysicsServer2D.area_add_shape(area, shape)
	PhysicsServer2D.area_set_space(area, space)
	var other_body := PhysicsServer2D.body_create()
	PhysicsServer2D.body_set_space(other_body, next_space)
	var joint := PhysicsServer2D.joint_create()
	PhysicsServer2D.joint_make_pin(joint, Vector2.ZERO, bodies[2], bodies[3])
	var direct_state := PhysicsServer2D.space_get_direct_state(space)
	assert(is_instance_valid(direct_state))
	PhysicsServer2D.free_rid(space)
	assert(not is_instance_valid(direct_state), "Freeing a space frees its direct state")
	assert(PhysicsServer2D.area_get_space(area) == RID())
	assert(PhysicsServer2D.area_get_shape_count(area) == 1)
	assert(PhysicsServer2D.body_get_space(other_body) == next_space)
	for i in bodies.size():
		assert(PhysicsServer2D.body_get_space(bodies[i]) == RID())
		assert(PhysicsServer2D.body_get_shape_count(bodies[i]) == 1)
		assert(PhysicsServer2D.body_get_state(bodies[i], PhysicsServer2D.BODY_STATE_TRANSFORM)
			== Transform2D(0, Vector2(i * 20, 0)))
		PhysicsServer2D.body_set_space(bodies[i], next_space)
		assert(PhysicsServer2D.body_get_space(bodies[i]) == next_space)
	PhysicsServer2D.area_set_space(area, next_space)
	PhysicsServer2D.pin_joint_set_param(joint, PhysicsServer2D.PIN_JOINT_SOFTNESS, 0.5)
	PhysicsServer2D.joint_make_pin(joint, Vector2.ZERO, bodies[2], bodies[3])
	PhysicsServer2D.space_set_active(next_space, true)
	await wait_physics_frames(3)
	var point := PhysicsPointQueryParameters2D.new()
	var hits := PhysicsServer2D.space_get_direct_state(next_space).intersect_point(point)
	assert(hits.size() == 1 and hits[0].rid == bodies[0], "Reattached body recreates its collider")
	PhysicsServer2D.free_rid(next_space)
	for body in bodies:
		assert(PhysicsServer2D.body_get_space(body) == RID())
		PhysicsServer2D.free_rid(body)
	PhysicsServer2D.free_rid(other_body)
	PhysicsServer2D.free_rid(area)
	PhysicsServer2D.free_rid(joint)
	PhysicsServer2D.free_rid(shape)


# State sync runs before monitor callbacks. Destroy the space with both kinds of
# callbacks queued, then reuse its objects without dispatching stale overlap events.
func test_state_sync_frees_space_with_pending_monitors() -> void:
	print("test_state_sync_frees_space_with_pending_monitors")
	var space := PhysicsServer2D.space_create()
	var shape := PhysicsServer2D.circle_shape_create()
	PhysicsServer2D.shape_set_data(shape, 10.0)
	var body := PhysicsServer2D.body_create()
	PhysicsServer2D.body_set_mode(body, PhysicsServer2D.BODY_MODE_RIGID)
	PhysicsServer2D.body_add_shape(body, shape)
	PhysicsServer2D.body_set_space(body, space)
	var area := PhysicsServer2D.area_create()
	PhysicsServer2D.area_add_shape(area, shape)
	PhysicsServer2D.area_set_space(area, space)
	var events: Array[int] = []
	PhysicsServer2D.area_set_monitor_callback(area,
		func(status: int, _body: RID, _instance: int, _body_shape: int, _area_shape: int):
			events.append(status))
	var calls := [0]
	PhysicsServer2D.body_set_state_sync_callback(body, func(_state: PhysicsDirectBodyState2D):
		calls[0] += 1
		PhysicsServer2D.free_rid(space))
	PhysicsServer2D.space_set_active(space, true)
	await wait_physics_frames(4)
	assert(calls[0] == 1)
	assert(events.is_empty(), "Destroyed space cancels pending monitor callbacks")
	assert(PhysicsServer2D.body_get_space(body) == RID())
	assert(PhysicsServer2D.area_get_space(area) == RID())
	PhysicsServer2D.body_set_state_sync_callback(body, Callable())
	var next_space := PhysicsServer2D.space_create()
	PhysicsServer2D.body_set_space(body, next_space)
	PhysicsServer2D.area_set_space(area, next_space)
	PhysicsServer2D.space_set_active(next_space, true)
	await wait_physics_frames(4)
	assert(events == [PhysicsServer2D.AREA_BODY_ADDED], "Reattached area reports a fresh overlap")
	PhysicsServer2D.free_rid(next_space)
	PhysicsServer2D.free_rid(area)
	PhysicsServer2D.free_rid(body)
	PhysicsServer2D.free_rid(shape)


# Fluids have no built-in counterpart. Exercise the extension API dynamically so
# the collision-object tests can also run without the extension loaded.
func test_free_space_detaches_fluid() -> void:
	print("test_free_space_detaches_fluid")
	var space := PhysicsServer2D.space_create()
	var fluid: RID = ClassDB.class_call_static(&"RapierPhysicsServer2D", &"fluid_create")
	ClassDB.class_call_static(&"RapierPhysicsServer2D", &"fluid_set_space", fluid, space)
	var points := PackedVector2Array([Vector2(10, 10)])
	ClassDB.class_call_static(&"RapierPhysicsServer2D", &"fluid_set_points", fluid, points)
	assert(ClassDB.class_call_static(&"RapierPhysicsServer2D", &"fluid_get_points", fluid) == points)
	PhysicsServer2D.free_rid(space)
	assert(ClassDB.class_call_static(&"RapierPhysicsServer2D", &"fluid_get_points", fluid) == points)
	var next_space := PhysicsServer2D.space_create()
	ClassDB.class_call_static(&"RapierPhysicsServer2D", &"fluid_set_space", fluid, next_space)
	assert(ClassDB.class_call_static(&"RapierPhysicsServer2D", &"fluid_get_points", fluid) == points)
	PhysicsServer2D.free_rid(next_space)
	PhysicsServer2D.free_rid(fluid)
