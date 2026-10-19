extends TestBase

signal completed

var done := false

func _ready():
	add_to_group(&"async_unit_tests")
	test_space_functions()
	await test_shape_query_result_limit()
	await test_query_collider_object()
	print("Space tests passed.")
	done = true
	completed.emit()


func test_space_functions():
	var space := PhysicsServer2D.space_create()
	assert(space != null)
	var direct_state = PhysicsServer2D.space_get_direct_state(space)
	assert(direct_state != null)
	var is_active = PhysicsServer2D.space_is_active(space)
	assert(is_active == false)
	PhysicsServer2D.space_set_active(space, true)
	is_active = PhysicsServer2D.space_is_active(space)
	assert(is_active == true)
	PhysicsServer2D.free_rid(space)
	direct_state = PhysicsServer2D.space_get_direct_state(space)
	assert(direct_state == null)


func test_shape_query_result_limit() -> void:
	var space := PhysicsServer2D.space_create()
	var shape := PhysicsServer2D.circle_shape_create()
	PhysicsServer2D.shape_set_data(shape, 10.0)
	var bodies: Array[RID] = []
	for i in range(80):
		var body := PhysicsServer2D.body_create()
		PhysicsServer2D.body_set_mode(body, PhysicsServer2D.BODY_MODE_STATIC)
		PhysicsServer2D.body_add_shape(body, shape)
		PhysicsServer2D.body_set_collision_mask(body, 0)
		PhysicsServer2D.body_set_space(body, space)
		bodies.append(body)
	PhysicsServer2D.space_set_active(space, true)
	await get_tree().physics_frame
	await get_tree().physics_frame
	var state := PhysicsServer2D.space_get_direct_state(space)
	var query := PhysicsShapeQueryParameters2D.new()
	query.shape_rid = shape
	var counts: Array[int] = []
	for maximum in [1, 3, 128]:
		counts.append(state.intersect_shape(query, maximum).size())
	for body in bodies:
		PhysicsServer2D.free_rid(body)
	PhysicsServer2D.free_rid(shape)
	PhysicsServer2D.free_rid(space)
	assert(counts == [1, 3, 80], "Shape query honors caller result limits")


func test_query_collider_object() -> void:
	var space := PhysicsServer2D.space_create()
	var shape := PhysicsServer2D.circle_shape_create()
	PhysicsServer2D.shape_set_data(shape, 10.0)
	var body := PhysicsServer2D.body_create()
	PhysicsServer2D.body_set_mode(body, PhysicsServer2D.BODY_MODE_STATIC)
	PhysicsServer2D.body_add_shape(body, shape)
	var object := RefCounted.new()
	PhysicsServer2D.body_attach_object_instance_id(body, object.get_instance_id())
	PhysicsServer2D.body_set_space(body, space)
	PhysicsServer2D.space_set_active(space, true)
	await get_tree().physics_frame
	await get_tree().physics_frame
	var state := PhysicsServer2D.space_get_direct_state(space)
	var ray := PhysicsRayQueryParameters2D.create(Vector2(-20, 0), Vector2(20, 0))
	var point := PhysicsPointQueryParameters2D.new()
	var query := PhysicsShapeQueryParameters2D.new()
	query.shape_rid = shape
	var ray_result := state.intersect_ray(ray)
	var point_results := state.intersect_point(point, 1)
	var shape_results := state.intersect_shape(query, 1)
	PhysicsServer2D.free_rid(body)
	PhysicsServer2D.free_rid(shape)
	PhysicsServer2D.free_rid(space)
	assert(ray_result.get("collider") == object, "Ray query resolves RefCounted collider")
	assert(ray_result.collider_id == object.get_instance_id())
	assert(point_results.size() == 1 and point_results[0].collider == object, "Point query resolves RefCounted collider")
	assert(point_results[0].collider_id == object.get_instance_id())
	assert(shape_results.size() == 1 and shape_results[0].collider == object, "Shape query resolves RefCounted collider")
	assert(shape_results[0].collider_id == object.get_instance_id())
