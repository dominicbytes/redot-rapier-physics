extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	assert(await run(root), "Regression test did not complete")
	print("EXPECTED DIAGNOSTICS TEST: SUCCESS")
	quit(0)


func run(host: Node) -> bool:
	var fluid = ClassDB.instantiate("Fluid2D")
	host.add_child(fluid)
	fluid.set_points_and_velocities(PackedVector2Array([Vector2(10, 10)]), PackedVector2Array([Vector2.ZERO]))
	for method in ["fluid_set_points_and_velocities", "fluid_add_points_and_velocities"]:
		for arrays in [[PackedVector2Array([Vector2(30, 10)]), PackedVector2Array()], [PackedVector2Array(), PackedVector2Array([Vector2.ONE])]]:
			var points: PackedVector2Array = fluid.get_points()
			var velocities: PackedVector2Array = fluid.get_velocities()
			var accelerations: PackedVector2Array = fluid.get_accelerations()
			if method == "fluid_set_points_and_velocities":
				RapierPhysicsServer2D.fluid_set_points_and_velocities(fluid.rid, arrays[0], arrays[1])
			else:
				RapierPhysicsServer2D.fluid_add_points_and_velocities(fluid.rid, arrays[0], arrays[1])
			assert(fluid.get_points() == points, "Rejected fluid input changed positions")
			assert(fluid.get_velocities() == velocities, "Rejected fluid input changed velocities")
			assert(fluid.get_accelerations() == accelerations, "Rejected fluid input changed accelerations")
	for frame in 3:
		await host.get_tree().physics_frame
	assert(fluid.get_points().size() == 1)
	assert(fluid.get_velocities().size() == 1)
	assert(fluid.get_accelerations().size() == 1)
	fluid.free()
	return true
