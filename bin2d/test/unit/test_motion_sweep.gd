extends Node2D

var passed := true

func check_motion(body: RID, label: String, origin: Vector2, motion: Vector2, blocked: bool, normal: Vector2 = Vector2.ZERO):
	var parameters := PhysicsTestMotionParameters2D.new()
	parameters.from = Transform2D(0, origin)
	parameters.motion = motion
	var result := PhysicsTestMotionResult2D.new()
	var collided := PhysicsServer2D.body_test_motion(body, parameters, result)
	print("SWEEP ", label, " collided=", collided, " travel=", result.get_travel(), " safe=", result.get_collision_safe_fraction(), " unsafe=", result.get_collision_unsafe_fraction(), " normal=", result.get_collision_normal())
	passed = passed and collided == blocked
	if blocked:
		passed = passed and result.get_travel().dot(-normal) <= 8.01 and result.get_travel().dot(-normal) >= maxf(6.0, 8.0 - motion.length() / 128.0 - 0.1)
		passed = passed and result.get_collision_normal().dot(normal) > 0.99
		passed = passed and result.get_collision_safe_fraction() <= result.get_collision_unsafe_fraction()
	else:
		passed = passed and result.get_travel().is_equal_approx(motion)

func _ready():
	var space := PhysicsServer2D.space_create()
	var circle := PhysicsServer2D.circle_shape_create()
	PhysicsServer2D.shape_set_data(circle, 1.0)
	var rectangle := PhysicsServer2D.rectangle_shape_create()
	PhysicsServer2D.shape_set_data(rectangle, Vector2(1, 100))
	var body := PhysicsServer2D.body_create()
	PhysicsServer2D.body_set_mode(body, PhysicsServer2D.BODY_MODE_KINEMATIC)
	PhysicsServer2D.body_add_shape(body, circle)
	PhysicsServer2D.body_set_space(body, space)
	for angle in [0.0, 0.3, -0.6]:
		var direction := Vector2.RIGHT.rotated(angle)
		var wall := PhysicsServer2D.body_create()
		PhysicsServer2D.body_set_mode(wall, PhysicsServer2D.BODY_MODE_STATIC)
		PhysicsServer2D.body_add_shape(wall, rectangle)
		PhysicsServer2D.body_set_state(wall, PhysicsServer2D.BODY_STATE_TRANSFORM, Transform2D(angle, direction * 10.0))
		PhysicsServer2D.body_set_space(wall, space)
		if PhysicsServer2D.get_class() == "RapierPhysicsServer2D":
			RapierPhysicsServer2D.space_step(space, 1.0 / 60.0)
		for speed in [20.0, 100.0, 1000.0]:
			check_motion(body, "wall_%s_%s" % [angle, speed], Vector2.ZERO, direction * speed + direction.orthogonal() * 3.0, true, -direction)
			check_motion(body, "reverse_wall_%s_%s" % [angle, speed], direction * 20.0, -direction * speed + direction.orthogonal() * 3.0, true, direction)
		check_motion(body, "tangent_%s" % angle, direction * 7.9, direction.orthogonal() * 20.0, false)
		PhysicsServer2D.free_rid(wall)
	var platform := PhysicsServer2D.body_create()
	PhysicsServer2D.body_set_mode(platform, PhysicsServer2D.BODY_MODE_STATIC)
	var platform_shape := PhysicsServer2D.rectangle_shape_create()
	PhysicsServer2D.shape_set_data(platform_shape, Vector2(100, 1))
	PhysicsServer2D.body_add_shape(platform, platform_shape)
	PhysicsServer2D.body_set_shape_as_one_way_collision(platform, 0, true, 1.0)
	PhysicsServer2D.body_set_state(platform, PhysicsServer2D.BODY_STATE_TRANSFORM, Transform2D(0, Vector2(0, 10)))
	PhysicsServer2D.body_set_space(platform, space)
	if PhysicsServer2D.get_class() == "RapierPhysicsServer2D":
		RapierPhysicsServer2D.space_step(space, 1.0 / 60.0)
	# Match the built-in swept-volume side check for longer downward casts.
	for angle in [0.0, 0.3, -0.6]:
		var direction := Vector2.DOWN.rotated(angle)
		PhysicsServer2D.body_set_state(platform, PhysicsServer2D.BODY_STATE_TRANSFORM, Transform2D(angle, direction * 10.0))
		if PhysicsServer2D.get_class() == "RapierPhysicsServer2D":
			RapierPhysicsServer2D.space_step(space, 1.0 / 60.0)
		for speed in [20.0, 100.0, 1000.0]:
			check_motion(body, "one_way_down_%s_%s" % [angle, speed], Vector2.ZERO, direction * speed, speed == 20.0, -direction)
			check_motion(body, "one_way_up_%s_%s" % [angle, speed], direction * 20.0, -direction * speed, false)
	for rid in [body, platform, circle, rectangle, platform_shape, space]:
		PhysicsServer2D.free_rid(rid)
	await test_character_slide()
	assert(passed, "Body sweeps must find the first impact across the entire motion")
	print("Motion sweep tests passed.")

func test_character_slide():
	await get_tree().physics_frame
	var wall := StaticBody2D.new()
	var wall_collision := CollisionShape2D.new()
	var wall_shape := RectangleShape2D.new()
	wall_shape.size = Vector2(2, 100)
	wall_collision.shape = wall_shape
	wall.add_child(wall_collision)
	wall.position = Vector2(10, 0)
	add_child(wall)
	var character := CharacterBody2D.new()
	var collision := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = 1.0
	collision.shape = circle
	character.add_child(collision)
	add_child(character)
	if PhysicsServer2D.get_class() == "RapierPhysicsServer2D":
		RapierPhysicsServer2D.space_step(get_world_2d().space, 1.0 / 60.0)
	character.velocity = Vector2(1200, 240)
	var collided := character.move_and_slide()
	print("CHARACTER SLIDE collided=", collided, " position=", character.position, " velocity=", character.velocity)
	passed = passed and collided and character.position.x < 8.01 and character.position.x > 7.5
	passed = passed and character.position.y > 3.5 and absf(character.velocity.x) < 0.1
	character.free()
	wall.free()
