extends Node2D

const EXPECTED_BACKEND := "Rapier2D"
const EXTENSION_CLASSES := [
	"RapierPhysicsServer2D",
	"RapierDirectBodyState2D",
	"RapierDirectSpaceState2D",
	"RapierMath2D",
	"Fluid2D",
	"FluidEffect2D",
	"FluidEffect2DElasticity",
	"FluidEffect2DSurfaceTensionAKINCI",
	"FluidEffect2DSurfaceTensionHE",
	"FluidEffect2DSurfaceTensionWCSPH",
	"FluidEffect2DViscosityArtificial",
	"FluidEffect2DViscosityDFSPH",
	"FluidEffect2DViscosityXSPH",
	"StateManager2D",
]
const SCRIPT_CLASSES := [
	"Faucet2D",
	"Fluid2DRenderer",
	"Fluid2DShaderRenderer",
	"RapierAnimatableBody2D",
	"RapierArea2D",
	"RapierCharacterBody2D",
	"RapierDampedSpringJoint2D",
	"RapierFixedJoint2D",
	"RapierGrooveJoint2D",
	"RapierPhysicalBone2D",
	"RapierPinJoint2D",
	"RapierRigidBody2D",
	"RapierRopeJoint2D",
	"RapierStaticBody2D",
]
const REQUIRED_METHODS := {
	"Fluid2D": [
		"set_points", "set_density", "set_lifetime", "set_effects",
		"get_points", "get_velocities", "get_accelerations", "get_remaining_times",
		"create_rectangle_points", "create_circle_points", "add_points_and_velocities",
		"set_points_and_velocities", "delete_points", "get_particles_in_aabb",
		"get_particles_in_circle", "set_collision_layer", "get_collision_layer",
		"set_collision_mask", "get_collision_mask",
	],
	"StateManager2D": [
		"cache_state", "load_cached_state", "export_state", "export_state_from_cache",
		"import_state", "ordered_cache_tags", "clear_cache", "remove_cached_by_index",
		"set_max_cache_length", "get_max_cache_length",
	],
	"RapierPhysicsServer2D": [
		"body_set_extra_param", "body_get_extra_param", "body_set_contact_force_threshold",
		"body_get_contact_force_threshold", "body_get_contact_tangent_impulse",
		"body_get_total_contact_impulse", "body_get_max_contact_impulse",
		"body_get_total_friction_impulse", "bodies_get_contact_impulse",
		"body_get_kinetic_energy", "body_is_ccd_active", "joint_get_reaction_impulse",
		"joint_get_reaction_angular_impulse", "joint_set_extra_param",
		"joint_get_extra_param", "joint_solve_inverse_kinematics", "joint_set_ik_options",
		"joint_reset_ik_options", "joint_set_motor_position_options", "joint_set_softness",
		"joint_set_enabled", "joint_make_rope", "joint_make_fixed", "fluid_create",
		"fluid_set_space", "fluid_set_density", "fluid_set_effects", "fluid_get_points",
		"fluid_get_velocities", "fluid_get_accelerations", "fluid_get_particles_in_aabb",
		"fluid_get_particles_in_ball", "fluid_get_collision_mask",
		"fluid_set_collision_masks", "fluid_get_collision_layer", "fluid_set_points",
		"fluid_set_points_and_velocities", "fluid_add_points_and_velocities",
		"fluid_delete_points", "space_get_active_bodies", "space_get_bodies_transform",
		"space_step", "space_flush_queries", "get_rapier_id", "get_global_id",
		"set_global_id", "get_stats",
	],
	"RapierMath2D": [
		"acos", "acosh", "asin", "asinh", "atan", "atanh", "atan2", "cbrt",
		"cos", "cosh", "exp", "exp2", "hypot", "log", "log2", "log10",
		"pow", "sin", "sinh", "sqrt", "tan", "tanh",
	],
}
const REQUIRED_SETTINGS := [
	"physics/rapier/solver/num_iterations",
	"physics/rapier/solver/num_internal_stabilization_iterations",
	"physics/rapier/solver/num_internal_pgs_iterations",
	"physics/rapier/solver/max_ccd_substeps",
	"physics/rapier/solver/normalized_allowed_linear_error",
	"physics/rapier/solver/normalized_max_corrective_velocity",
	"physics/rapier/solver/normalized_prediction_distance",
	"physics/rapier/solver/normalized_max_linear_velocity",
	"physics/rapier/solver/predictive_contact_allowance_threshold",
	"physics/rapier/solver/contact_damping_ratio",
	"physics/rapier/solver/contact_natural_frequency",
	"physics/rapier/solver/length_unit_2d",
	"physics/rapier/motion/recover_attempts",
	"physics/rapier/motion/recover_ratio",
	"physics/rapier/motion/cast_iterations",
	"physics/rapier/motion/stuck_penetration_threshold_2d",
	"physics/rapier/queries/max_shape_cast_results",
	"physics/rapier/queries/point_query_honors_pickable",
	"physics/rapier/shapes/scale_subdivisions",
	"physics/rapier/fluid/fluid_particle_radius_2d",
	"physics/rapier/fluid/fluid_smoothing_factor",
	"physics/rapier/fluid/fluid_boundary_coefficient",
	"physics/rapier/logic/oriented_concave_polyline_2d",
]


func _ready() -> void:
	call_deferred("_run")


func _fail(message: String) -> bool:
	push_error(message)
	print("REDOT RAPIER2D FEATURE PARITY: FAILED")
	get_tree().quit(1)
	return false


func _run() -> void:
	if str(ProjectSettings.get_setting("physics/2d/physics_engine", "")) != EXPECTED_BACKEND:
		_fail("Rapier2D is not the selected backend")
		return
	if not _check_registered_surface():
		return
	if not await _check_fluid_surface():
		return
	if not await _check_state_serialization():
		return
	print("REDOT RAPIER2D FEATURE PARITY: SUCCESS")
	get_tree().quit(0)


func _check_registered_surface() -> bool:
	for extension_class in EXTENSION_CLASSES:
		if not ClassDB.class_exists(extension_class):
			return _fail("Missing GDExtension class: %s" % extension_class)

	var global_classes := {}
	for entry in ProjectSettings.get_global_class_list():
		global_classes[str(entry.get("class", ""))] = true
	for script_class in SCRIPT_CLASSES:
		if not global_classes.has(script_class):
			return _fail("Missing addon script class: %s" % script_class)

	for extension_class in REQUIRED_METHODS:
		var methods := {}
		for method in ClassDB.class_get_method_list(extension_class):
			methods[str(method.get("name", ""))] = true
		for method_name in REQUIRED_METHODS[extension_class]:
			if not methods.has(method_name):
				return _fail("Missing %s.%s" % [extension_class, method_name])

	for setting_name in REQUIRED_SETTINGS:
		if not ProjectSettings.has_setting(setting_name):
			return _fail("Missing project setting: %s" % setting_name)
	return true


func _check_fluid_surface() -> bool:
	var fluid := ClassDB.instantiate("Fluid2D") as Node2D
	if fluid == null:
		return _fail("Fluid2D could not be instantiated")
	add_child(fluid)
	fluid.set("density", 2.0)
	fluid.set("lifetime", 10.0)
	fluid.call("set_collision_layer", 3)
	fluid.call("set_collision_mask", 5)
	if fluid.call("get_collision_layer") != 3 or fluid.call("get_collision_mask") != 5:
		fluid.queue_free()
		return _fail("Fluid2D collision filters did not round-trip")

	var effects: Array[Resource] = []
	for extension_class in EXTENSION_CLASSES:
		if extension_class.begins_with("FluidEffect2D") and extension_class != "FluidEffect2D":
			var effect := ClassDB.instantiate(extension_class) as Resource
			if effect == null:
				fluid.queue_free()
				return _fail("Fluid effect could not be instantiated: %s" % extension_class)
			effects.append(effect)
	# Instantiate every effect class, then simulate with one conservative viscosity
	# effect. Combining every model at its default strength is not a supported preset.
	var active_effects: Array[Resource] = [effects[-1]]
	fluid.call("set_effects", active_effects)

	var points: PackedVector2Array = fluid.call("create_rectangle_points", 3, 2)
	if points.size() != 6:
		fluid.queue_free()
		return _fail("Fluid2D rectangle generation returned %d particles" % points.size())
	var circle_points: PackedVector2Array = fluid.call("create_circle_points", 2)
	if circle_points.is_empty():
		fluid.queue_free()
		return _fail("Fluid2D circle generation returned no particles")
	var velocities := PackedVector2Array()
	velocities.resize(points.size())
	velocities.fill(Vector2(2.0, -1.0))
	fluid.call("set_points_and_velocities", points, velocities)
	await get_tree().physics_frame
	await get_tree().physics_frame
	if fluid.call("get_points").size() != 6:
		fluid.queue_free()
		return _fail("Fluid2D particle state was not retained")
	if fluid.call("get_velocities").size() != 6 or fluid.call("get_accelerations").size() != 6:
		fluid.queue_free()
		return _fail("Fluid2D velocity/acceleration state is incomplete")
	if fluid.call("get_remaining_times").size() != 6:
		fluid.queue_free()
		return _fail("Fluid2D lifetime state is incomplete")
	if fluid.call("get_particles_in_aabb", Rect2(-10000, -10000, 20000, 20000)).size() != 6:
		fluid.queue_free()
		return _fail("Fluid2D AABB query did not return all particles")
	if fluid.call("get_particles_in_circle", Vector2.ZERO, 10000.0).size() != 6:
		fluid.queue_free()
		return _fail("Fluid2D circle query did not return all particles")
	fluid.call("delete_points", PackedInt32Array([5]))
	await get_tree().physics_frame
	if fluid.call("get_points").size() != 5:
		fluid.queue_free()
		return _fail("Fluid2D particle deletion failed")
	fluid.queue_free()
	await get_tree().process_frame
	return true


func _check_state_serialization() -> bool:
	var fixture := Node2D.new()
	fixture.name = "StateFixture"
	add_child(fixture)
	var manager := ClassDB.instantiate("StateManager2D") as Node
	if manager == null:
		fixture.queue_free()
		return _fail("StateManager2D could not be instantiated")
	fixture.add_child(manager)
	manager.set("root_node", fixture)
	manager.call("set_max_cache_length", 2)

	var body := RigidBody2D.new()
	body.name = "SerializedBody"
	body.gravity_scale = 0.0
	body.can_sleep = false
	var collision_shape := CollisionShape2D.new()
	var rectangle := RectangleShape2D.new()
	rectangle.size = Vector2(32.0, 32.0)
	collision_shape.shape = rectangle
	body.add_child(collision_shape)
	body.position = Vector2(24.0, 48.0)
	fixture.add_child(body)
	await get_tree().physics_frame
	await get_tree().physics_frame

	var space := get_world_2d().space
	PhysicsServer2D.set_active(false)
	manager.call("cache_state", space, "checkpoint")
	var tags: Array = manager.call("ordered_cache_tags")
	if tags.size() != 1 or tags[0] != "checkpoint":
		fixture.queue_free()
		return _fail("StateManager2D cache tags did not round-trip")
	var json_state: Variant = manager.call("export_state_from_cache", -1, "Json")
	var base64_state: Variant = manager.call("export_state_from_cache", -1, "GodotBase64")
	var binary_state: Variant = manager.call("export_state_from_cache", -1, "RustBincode")
	PhysicsServer2D.set_active(true)
	if not json_state is String or (json_state as String).is_empty():
		fixture.queue_free()
		return _fail("StateManager2D JSON export failed")
	if not base64_state is String or (base64_state as String).is_empty():
		fixture.queue_free()
		return _fail("StateManager2D Base64 export failed")
	if not binary_state is PackedByteArray or (binary_state as PackedByteArray).is_empty():
		fixture.queue_free()
		return _fail("StateManager2D bincode export failed")

	body.position = Vector2(400.0, 500.0)
	await get_tree().physics_frame
	PhysicsServer2D.set_active(false)
	if not manager.call("load_cached_state", space, -1):
		PhysicsServer2D.set_active(true)
		fixture.queue_free()
		return _fail("StateManager2D cache restore returned false")
	PhysicsServer2D.set_active(true)
	await get_tree().process_frame
	await get_tree().physics_frame
	if not body.position.is_equal_approx(Vector2(24.0, 48.0)):
		var server_transform: Transform2D = PhysicsServer2D.body_get_state(
			body.get_rid(), PhysicsServer2D.BODY_STATE_TRANSFORM)
		fixture.queue_free()
		return _fail("StateManager2D cache restore mismatch: node=%s server=%s" % [
			body.position,
			server_transform.origin,
		])

	body.position = Vector2(700.0, 800.0)
	await get_tree().physics_frame
	PhysicsServer2D.set_active(false)
	manager.call("import_state", space, json_state)
	PhysicsServer2D.set_active(true)
	await get_tree().process_frame
	await get_tree().physics_frame
	if not body.position.is_equal_approx(Vector2(24.0, 48.0)):
		fixture.queue_free()
		return _fail("StateManager2D serialized import did not restore the body transform")
	manager.call("remove_cached_by_index", -1)
	if not (manager.call("ordered_cache_tags") as Array).is_empty():
		fixture.queue_free()
		return _fail("StateManager2D cache removal failed")
	manager.call("clear_cache")
	fixture.queue_free()
	await get_tree().process_frame
	await get_tree().physics_frame
	return true
