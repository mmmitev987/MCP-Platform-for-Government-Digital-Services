# shared/ — Institution-agnostic infrastructure layer.
#
# Every class here is parameterized: it accepts institution-specific values
# (URLs, file paths, encryption keys) in its constructor rather than reading
# them from a fixed config module.  Each institution in institutions/ creates
# its own instance with its own settings.
#
# This means the logic lives here ONCE, and there is no copy-pasting between
# institutions when new ones are added.
