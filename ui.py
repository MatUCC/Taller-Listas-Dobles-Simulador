"""In-game GUI: simulation telemetry, tunable Boids parameters and controls."""
from __future__ import annotations

from ursina import Button, Entity, Text, Slider, color, camera


class ControlPanel:
    """Creates a compact dashboard entirely with Ursina UI prefabs."""

    def __init__(self, config, flock, environment, camera_controller):
        self.cfg = config
        self.flock = flock
        self.environment = environment
        self.camera_controller = camera_controller
        self.enabled = True
        self.root = Entity(parent=camera.ui, x=-0.86, y=0.47, scale=(0.29, 0.9))
        Entity(parent=self.root, model="quad", color=color.rgba(12, 17, 22, 210), scale=(1.02, 1.02), z=1)
        self.stats = Text(parent=self.root, text="", x=-0.45, y=0.47, origin=(-0.5, 0.5), scale=0.75)
        Text(parent=self.root, text="STARLING FLOCK / BOIDS", x=-0.45, y=0.43, scale=0.85)

        self.sliders = {}
        slider_specs = [
            ("Separation", "separation_weight", 0, 4, config.separation_weight),
            ("Alignment", "alignment_weight", 0, 3, config.alignment_weight),
            ("Cohesion", "cohesion_weight", 0, 3, config.cohesion_weight),
            ("Predator", "predator_weight", 0, 6, config.predator_weight),
            ("Obstacle", "obstacle_weight", 0, 6, config.obstacle_weight),
            ("Seek food", "seek_weight", 0, 3, config.seek_weight),
        ]
        for i, (label, attr, lo, hi, default) in enumerate(slider_specs):
            y = 0.32 - i * 0.062
            Text(parent=self.root, text=label, x=-0.45, y=y + 0.017, scale=0.65)
            s = Slider(parent=self.root, min=lo, max=hi, default=default, dynamic=True, x=-0.03, y=y, scale=(0.8, 1, 1))
            # Ursina Slider invokes on_value_changed() without arguments.
            s.on_value_changed = lambda a=attr, slider=s: setattr(self.cfg, a, slider.value)
            self.sliders[attr] = s

        self.toggle_vectors_button = Button(parent=self.root, text="Vectors: OFF", x=-0.42, y=-0.10, scale=(0.34, 0.06), color=color.azure.tint(-0.45))
        self.toggle_vectors_button.on_click = self._toggle_vectors
        self.follow_button = Button(parent=self.root, text="Camera: ORBIT", x=-0.05, y=-0.10, scale=(0.34, 0.06), color=color.lime.tint(-0.50))
        self.follow_button.on_click = self._toggle_camera
        self.add_button = Button(parent=self.root, text="+ Bird", x=-0.31, y=-0.18, scale=(0.22, 0.06))
        self.add_button.on_click = self.flock.add_bird
        self.remove_button = Button(parent=self.root, text="- Bird", x=-0.05, y=-0.18, scale=(0.22, 0.06))
        self.remove_button.on_click = self.flock.remove_bird
        self.rock_button = Button(parent=self.root, text="Spawn obstacle", x=-0.20, y=-0.26, scale=(0.44, 0.06), color=color.orange.tint(-0.45))
        self.rock_button.on_click = self.environment.spawn_obstacle
        self.hide_button = Button(parent=self.root, text="HIDE UI [TAB]", x=-0.20, y=-0.34, scale=(0.44, 0.055))
        self.hide_button.on_click = self.toggle

        self.help = Text(parent=camera.ui, text="TAB UI   |   C follow/orbit   |   N next bird   |   V vectors   |   WASD camera", x=-0.49, y=-0.48, origin=(0, 0), scale=0.75)

    def _toggle_vectors(self) -> None:
        self.flock.show_vectors = not self.flock.show_vectors
        self.toggle_vectors_button.text = f"Vectors: {'ON' if self.flock.show_vectors else 'OFF'}"

    def _toggle_camera(self) -> None:
        self.camera_controller.toggle_mode()
        self.follow_button.text = f"Camera: {self.camera_controller.mode.upper()}"

    def toggle(self) -> None:
        self.enabled = not self.enabled
        self.root.enabled = self.enabled
        self.help.enabled = self.enabled

    def update(self) -> None:
        avg_speed = self.flock.average_speed()
        avg_energy = self.flock.average_energy()
        nearest = self.flock.nearest_predator_distance()
        self.stats.text = (
            f"Birds     {len(self.flock.birds):03d}\n"
            f"Avg speed {avg_speed:5.1f} m/s\n"
            f"Avg energy{avg_energy:5.1f} %\n"
            f"Predator  {nearest:5.1f} m\n"
            f"Wind      {self.cfg.wind_strength:5.1f} m/s"
        )
