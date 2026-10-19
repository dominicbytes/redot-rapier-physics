extends Node

# Isolate the inherited synchronous assertions so a failed child callback cannot
# resume this wrapper and print SUCCESS. Capture stderr as well as stdout.
func _ready() -> void:
	var output: Array = []
	var status := OS.execute(OS.get_executable_path(), PackedStringArray([
		"--headless", "--audio-driver", "Dummy", "--fixed-fps", "60",
		"--path", ProjectSettings.globalize_path("res://"),
		"--scene", "res://test/unit/api_tests.tscn", "--quit-after", "1200",
	]), output, true)
	var text := "\n".join(output)
	print(text)
	for diagnostic in ["SCRIPT ERROR", "Parse Error", "Assertion failed", "ERROR:",
			"GDExtension initialization", "Failed to load", "panicked at"]:
		if diagnostic.to_lower() in text.to_lower():
			status = 1
	if status != 0:
		print("UNIT TESTS STATUS: FAILED")
		get_tree().quit(1)
		return
	print("UNIT TESTS STATUS: SUCCESS")
	get_tree().quit(0)
