extends RefCounted

func run() -> void:
	var shape := PhysicsServer2D.world_boundary_shape_create()
	for normal in [Vector2.UP, Vector2.RIGHT, Vector2(0.6, 0.8), Vector2(0, -2)]:
		for distance in [-100.0, 0.0, 100.0]:
			var expected := [normal, distance]
			PhysicsServer2D.shape_set_data(shape, expected)
			assert(PhysicsServer2D.shape_get_data(shape) == expected, "World boundary data must round-trip unchanged")
	PhysicsServer2D.free_rid(shape)
	print("World boundary tests passed.")
