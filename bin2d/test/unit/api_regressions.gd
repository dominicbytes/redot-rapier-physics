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
	_run_expected_errors("res://test/unit/test_fluid_array_lengths.gd", "Points and velocities must have the same length.", 4)
	# Wait for scene tests that run across physics frames.
	for test in get_tree().get_nodes_in_group(&"async_unit_tests"):
		while not test.done:
			await get_tree().physics_frame
	_completed = true
	print("API regression tests completed.")

# Invalid-input tests deliberately emit errors. Require those exact diagnostics
# and completion in a child process, and reject every unexpected error.
func _run_expected_errors(script: String, expected: String, count: int) -> void:
	var output: Array = []
	var status := OS.execute(OS.get_executable_path(), PackedStringArray([
		"--headless", "--audio-driver", "Dummy", "--fixed-fps", "60",
		"--path", ProjectSettings.globalize_path("res://"),
		"--script", script, "--quit-after", "120",
	]), output, true)
	var text := "\n".join(output)
	assert(status == 0, "Invalid-input child process failed")
	assert("EXPECTED DIAGNOSTICS TEST: SUCCESS" in text, "Invalid-input test did not complete")
	assert(text.count("ERROR: " + expected) == count, "Expected rejection diagnostics are missing")
	text = text.replace("ERROR: " + expected, "")
	for diagnostic in ["SCRIPT ERROR", "Parse Error", "Assertion failed", "ERROR:",
			"GDExtension initialization", "Failed to load", "panicked at"]:
		assert(not diagnostic.to_lower() in text.to_lower(), "Unexpected invalid-input child diagnostic")
	print(script.get_file(), " passed with expected rejection diagnostics.")
