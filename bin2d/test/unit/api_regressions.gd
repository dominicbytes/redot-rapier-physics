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
	# Wait for scene tests that run across physics frames.
	for test in get_tree().get_nodes_in_group(&"async_unit_tests"):
		while not test.done:
			await get_tree().physics_frame
	_completed = true
	print("API regression tests completed.")
