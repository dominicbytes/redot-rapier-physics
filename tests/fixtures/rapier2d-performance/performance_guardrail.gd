extends Node2D

const SENTINEL := "REDOT RAPIER2D PERFORMANCE SAMPLE: SUCCESS"
const RAPIER_BACKEND := "Rapier2D"

var _bodies: Array[RigidBody2D] = []
var _initial_positions: Array[Vector2] = []
var _fluid: Node2D


func _ready() -> void:
	call_deferred("_run")


func _argument(name: String, fallback: String = "") -> String:
	var prefix := "--%s=" % name
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with(prefix):
			return argument.trim_prefix(prefix)
	return fallback


func _write_result(result: Dictionary) -> void:
	var output := _argument("result")
	if output.is_empty():
		push_error("Performance result path was not supplied")
		return
	var file := FileAccess.open(output, FileAccess.WRITE)
	if file == null:
		push_error("Could not write performance result: %s" % output)
		return
	file.store_string(JSON.stringify(result) + "\n")


func _fail(message: String) -> void:
	_write_result({"status": "FAIL", "message": message})
	push_error(message)
	get_tree().quit(1)


func _run() -> void:
	var scenario := _argument("scenario")
	var kind := _argument("kind")
	var count := _argument("count", "0").to_int()
	var columns := _argument("columns", "1").to_int()
	var warmup_frames := _argument("warmup", "120").to_int()
	var sample_frames := _argument("samples", "360").to_int()
	var selected_backend := str(ProjectSettings.get_setting(
		"physics/2d/physics_engine", "DEFAULT"))
	var expected_backend := str(ProjectSettings.get_setting("test/expected_backend", ""))
	if selected_backend != expected_backend:
		_fail("Expected backend %s, got %s" % [expected_backend, selected_backend])
		return
	if count <= 0 or columns <= 0 or warmup_frames < 1 or sample_frames < 1:
		_fail("Invalid performance scenario parameters")
		return
	if kind == "bodies":
		_setup_bodies(count, columns)
	elif kind == "fluid":
		if selected_backend != RAPIER_BACKEND:
			_fail("Fluid workload requires Rapier2D")
			return
		if not _setup_fluid(count, columns):
			return
	else:
		_fail("Unknown performance scenario kind: %s" % kind)
		return

	for frame in warmup_frames:
		await get_tree().physics_frame
	var physics_ms: Array[float] = []
	var static_memory_bytes: Array[int] = []
	for frame in sample_frames:
		var frame_started_usec := Time.get_ticks_usec()
		await get_tree().physics_frame
		var duration := float(Time.get_ticks_usec() - frame_started_usec) / 1000.0
		var memory := int(Performance.get_monitor(Performance.MEMORY_STATIC))
		if not is_finite(duration) or duration < 0.0 or memory < 0:
			_fail("Performance monitor returned invalid data")
			return
		physics_ms.append(duration)
		static_memory_bytes.append(memory)

	var correctness := _check_bodies(count) if kind == "bodies" else _check_fluid(count)
	if not bool(correctness.get("pass", false)):
		_fail(str(correctness.get("message", "Workload correctness failed")))
		return
	_write_result({
		"schema_version": 1,
		"status": "PASS",
		"scenario": scenario,
		"kind": kind,
		"requested_count": count,
		"columns": columns,
		"warmup_frames": warmup_frames,
		"sample_frames": sample_frames,
		"measurement": "wall-clock interval between consecutive physics-frame signals",
		"selected_backend": selected_backend,
		"observed": {
			"os": OS.get_name(),
			"architecture": Engine.get_architecture_name(),
			"redot_version": Engine.get_version_info(),
		},
		"physics_ms": physics_ms,
		"static_memory_bytes": static_memory_bytes,
		"correctness": correctness,
	})
	print(SENTINEL)
	get_tree().quit(0)


func _add_floor() -> void:
	var floor_body := StaticBody2D.new()
	floor_body.position = Vector2(0.0, 540.0)
	var collision := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(1800.0, 40.0)
	collision.shape = shape
	floor_body.add_child(collision)
	add_child(floor_body)


func _setup_bodies(count: int, columns: int) -> void:
	_add_floor()
	for index in count:
		var body := RigidBody2D.new()
		body.can_sleep = false
		body.position = Vector2(
			-420.0 + float(index % columns) * 12.0,
			40.0 - float(index / columns) * 12.0,
		)
		var collision := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = Vector2(10.0, 10.0)
		collision.shape = shape
		body.add_child(collision)
		add_child(body)
		_bodies.append(body)
		_initial_positions.append(body.position)


func _setup_fluid(count: int, columns: int) -> bool:
	_add_floor()
	_fluid = ClassDB.instantiate("Fluid2D") as Node2D
	if _fluid == null:
		_fail("Fluid2D is not registered")
		return false
	add_child(_fluid)
	var rows := ceili(float(count) / float(columns))
	var points: PackedVector2Array = _fluid.call("create_rectangle_points", columns, rows)
	if points.size() < count:
		_fail("Fluid2D did not generate the requested particle count")
		return false
	points.resize(count)
	for index in points.size():
		points[index] += Vector2(-420.0, 40.0)
	var velocities := PackedVector2Array()
	velocities.resize(count)
	velocities.fill(Vector2.ZERO)
	var viscosity := ClassDB.instantiate("FluidEffect2DViscosityXSPH") as Resource
	if viscosity == null:
		_fail("Fluid viscosity effect is not registered")
		return false
	var effects: Array[Resource] = [viscosity]
	_fluid.call("set_effects", effects)
	_fluid.call("set_points_and_velocities", points, velocities)
	return true


func _check_bodies(expected: int) -> Dictionary:
	if _bodies.size() != expected:
		return {"pass": false, "message": "Body count changed"}
	var moved := 0
	for index in _bodies.size():
		var body := _bodies[index]
		var position := body.position
		var velocity := body.linear_velocity
		if not is_finite(position.x) or not is_finite(position.y):
			return {"pass": false, "message": "Non-finite body position"}
		if not is_finite(velocity.x) or not is_finite(velocity.y):
			return {"pass": false, "message": "Non-finite body velocity"}
		if max(absf(position.x), absf(position.y)) > 10000000.0:
			return {"pass": false, "message": "Body escaped the bounded workload"}
		if position.distance_squared_to(_initial_positions[index]) > 1.0:
			moved += 1
	if moved < maxi(1, expected / 4):
		return {"pass": false, "message": "Too few bodies moved during the workload"}
	return {"pass": true, "body_count": expected, "moved_bodies": moved}


func _check_fluid(expected: int) -> Dictionary:
	var points: PackedVector2Array = _fluid.call("get_points")
	var velocities: PackedVector2Array = _fluid.call("get_velocities")
	if points.size() != expected or velocities.size() != expected:
		return {"pass": false, "message": "Fluid particle state changed size"}
	for index in points.size():
		if not is_finite(points[index].x) or not is_finite(points[index].y):
			return {"pass": false, "message": "Non-finite fluid position"}
		if not is_finite(velocities[index].x) or not is_finite(velocities[index].y):
			return {"pass": false, "message": "Non-finite fluid velocity"}
	return {"pass": true, "particle_count": expected}
