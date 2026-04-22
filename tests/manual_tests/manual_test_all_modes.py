from importlib import import_module

MODULES_TO_RUN = [
	"manual_test_calculate_dose_interactive",
	"manual_test_calculate_dose_static",
	"manual_test_plot_event",
	"manual_test_plot_procedure",
	"manual_test_plot_setup",
]

for module_name in MODULES_TO_RUN:
	import_module(module_name)

print("all modes executed")
