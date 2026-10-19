extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	assert(await run(root), "Regression test did not complete")
	print("EXPECTED DIAGNOSTICS TEST: SUCCESS")
	quit(0)


func run(host: Node) -> bool:
	var world := Node2D.new()
	host.add_child(world)
	var manager = ClassDB.instantiate("StateManager2D")
	host.add_child(manager)
	manager.root_node = world
	var space := world.get_world_2d().space
	for rolling in [true, false]:
		manager.rolling_cache = rolling
		manager.max_cache_length = 0
		manager.cache_state(space, "disabled-empty")
		assert(manager.ordered_cache_tags().is_empty())
		manager.max_cache_length = 1
		manager.cache_state(space, "enabled")
		assert(manager.ordered_cache_tags().size() == 1)
		manager.max_cache_length = 0
		manager.cache_state(space, "disabled-drained")
		assert(manager.ordered_cache_tags().is_empty())
	manager.max_cache_length = 2
	manager.rolling_cache = true
	for tag in [1, 2, 3]:
		manager.cache_state(space, tag)
	assert(manager.ordered_cache_tags() == [2, 3])
	manager.free()
	world.free()
	return true
