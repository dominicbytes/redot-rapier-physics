extends Node2D

var _completed := false
var _frames := 0

func _physics_process(_delta: float) -> void:
	_frames += 1
	if _frames == 1000 and not _completed:
		push_error("API regression tests did not finish within 1000 physics frames")

func _ready() -> void:
	await get_tree().physics_frame
	await preload("res://test/unit/test_shape_replacement.gd").new().run(get_tree())
	preload("res://test/unit/test_shape.gd").new().run()
	preload("res://test/unit/test_shape_collide_manifold.gd").new().run()
	preload("res://test/unit/test_world_boundary.gd").new().run()
	var custom_integrator_gravity := preload("res://test/unit/test_custom_integrator_gravity.gd").new()
	add_child(custom_integrator_gravity)
	assert(await custom_integrator_gravity.run(), "Custom integration must keep automatic gravity disabled")
	custom_integrator_gravity.queue_free()
	var area_override_refresh := preload("res://test/unit/test_area_override_refresh.gd").new()
	add_child(area_override_refresh)
	assert(await area_override_refresh.run(), "Body parameter changes must refresh overlapping area overrides")
	area_override_refresh.queue_free()
	var force_integration_argument := preload("res://test/unit/test_force_integration_argument.gd").new()
	add_child(force_integration_argument)
	assert(await force_integration_argument.run(), "Force integration callbacks must receive state and optional userdata")
	force_integration_argument.queue_free()
	_run_expected_diagnostics("res://test/unit/test_fluid_array_lengths.gd", "ERROR: Points and velocities must have the same length.", 4)
	assert(await preload("res://test/unit/test_snapshot_body_parameters.gd").new().run(self), "Regression test did not complete")
	assert(await preload("res://test/unit/test_snapshot_shape_data.gd").new().run(self), "Snapshot shape data must match restored geometry")
	_run_expected_diagnostics("res://test/unit/test_snapshot_contact_validation.gd", "ERROR: Invalid snapshot: body contact count exceeds stored contacts or is negative.", 2)
	_run_expected_diagnostics("res://test/unit/test_state_cache_zero_length.gd", "WARNING: Count of cached states exceeds the new maximum limit; the oldest 1 states will be removed.", 2)
	var point_picking := preload("res://test/unit/test_point_picking.gd").new()
	add_child(point_picking)
	assert(await point_picking.run(), "Point queries and viewport picking must honor the available engine context")
	point_picking.queue_free()
	# Wait for scene tests that run across physics frames.
	for test in get_tree().get_nodes_in_group(&"async_unit_tests"):
		while not test.done:
			await get_tree().physics_frame
	_completed = true
	print("API regression tests completed.")

# Some tests deliberately emit errors or warnings. Require those exact diagnostics
# and completion in a child process, and reject every unexpected diagnostic.
func _run_expected_diagnostics(script: String, expected: String, count: int) -> void:
	var output: Array = []
	var status := OS.execute(OS.get_executable_path(), PackedStringArray([
		"--headless", "--audio-driver", "Dummy", "--fixed-fps", "60",
		"--path", ProjectSettings.globalize_path("res://"),
		"--script", script, "--quit-after", "120",
	]), output, true)
	var text := "\n".join(output)
	assert(status == 0, "Expected-diagnostics child process failed")
	assert("EXPECTED DIAGNOSTICS TEST: SUCCESS" in text, "Expected-diagnostics test did not complete")
	assert(text.count(expected) == count, "Expected rejection diagnostics are missing")
	text = text.replace(expected, "")
	for diagnostic in ["SCRIPT ERROR", "Parse Error", "Assertion failed", "ERROR:", "WARNING:",
			"GDExtension initialization", "Failed to load", "panicked at"]:
		assert(not diagnostic.to_lower() in text.to_lower(), "Unexpected child diagnostic")
	print(script.get_file(), " passed with expected rejection diagnostics.")
