extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var fluid = ClassDB.instantiate("Fluid2D")
	root.add_child(fluid)
	var points := PackedVector2Array()
	for index in 64:
		points.append(Vector2(index % 8, floori(index / 8.0)) * 10.0)
	fluid.set_points(points)
	for frame in 3:
		await physics_frame
	assert(fluid.get_points().size() == 64, "Fluid solver did not preserve particles")
	fluid.free()
	print("WORKER SHUTDOWN TEST: SUCCESS")
	quit(0)
