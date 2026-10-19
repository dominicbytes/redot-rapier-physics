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
	await test_area_signal_creates_spaces()
	await test_state_sync_creates_spaces_and_frees_body()
	await test_monitor_callback_frees_space()
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
		# Detach both objects first, so this covers only freeing the space being flushed and
		# not freeing a space that still holds objects.
		PhysicsServer2D.body_set_space(body, RID())
		PhysicsServer2D.area_set_space(area, RID())
		PhysicsServer2D.free_rid(space)
	PhysicsServer2D.area_set_monitor_callback(area, monitor)

	await wait_physics_frames(5)
	assert(events == [PhysicsServer2D.AREA_BODY_ADDED])
	assert(PhysicsServer2D.area_get_space(area) == RID())
	assert(PhysicsServer2D.body_get_space(body) == RID())

	PhysicsServer2D.free_rid(area)
	PhysicsServer2D.free_rid(body)
	PhysicsServer2D.free_rid(shape)
