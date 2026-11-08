# Direct stock USB capability evidence

Question: can the exact shipped binary and read-only runtime observations establish the reporter features when the kernel config was not retained?

Status: one bounded offline symbol extraction and one read-only runtime filesystem/path query. This supplements the preceding config-only preflight; it does not invent a config file or provide deployment approval. No controller changes, root, image, reboot, build or flash.

Outputs: evidence.json contains actual linked symbols/initcall names and runtime observations. Continuation: decide whether the known-stock calibration is a valid control; distinguish direct capabilities from unavailable original config flags.

Actual linked stock symbols include configfs_init, gadget_cfs_init, fsg_alloc_inst/fsg_alloc and mass_storagemod_init, with init-function pointer references in the Image. Runtime /proc/filesystems lists configfs and tmpfs. This directly establishes implementation presence; the original .config and its literal flags remain unavailable. It is a reason to prepare the known-stock control, not proof that this reporter/configuration will work. Only the physical calibration can settle that.
