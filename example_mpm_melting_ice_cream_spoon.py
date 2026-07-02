# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

"""Ice cream sphere that gradually melts while being scooped.

This reuses the teaspoon scooping setup but updates MPM material parameters over
simulation time.  The material starts cohesive and yield-stress dominated, then
transitions to a softer, lower-friction, more fluid-like material.
"""

import newton
import newton.examples
from example_mpm_ice_cream_spoon import Example as SpoonExample


class Example(SpoonExample):
    def __init__(self, viewer, options):
        super().__init__(viewer, options)
        self.options = options
        self._update_melting_material(0.0)

    @staticmethod
    def _smoothstep(x):
        x = min(max(float(x), 0.0), 1.0)
        return x * x * (3.0 - 2.0 * x)

    def _melt_fraction(self, t):
        if self.options.melt_end <= self.options.melt_start:
            return 1.0
        return Example._smoothstep((t - self.options.melt_start) / (self.options.melt_end - self.options.melt_start))

    @staticmethod
    def _lerp(a, b, f):
        return float(a + f * (b - a))

    def _update_melting_material(self, t):
        f = self._melt_fraction(t)

        # Use the original ice-cream/spoon material arguments as the frozen state.
        viscosity = Example._lerp(self.options.viscosity, self.options.melted_viscosity, f)
        friction = Example._lerp(self.options.friction, self.options.melted_friction, f)
        young_modulus = Example._lerp(self.options.young_modulus, self.options.melted_young_modulus, f)
        damping = Example._lerp(self.options.damping, self.options.melted_damping, f)
        yield_pressure = Example._lerp(self.options.yield_pressure, self.options.melted_yield_pressure, f)
        yield_stress = Example._lerp(self.options.yield_stress, self.options.melted_yield_stress, f)

        self.model.mpm.viscosity.fill_(viscosity)
        self.model.mpm.friction.fill_(friction)
        self.model.mpm.young_modulus.fill_(young_modulus)
        self.model.mpm.damping.fill_(damping)
        self.model.mpm.yield_pressure.fill_(yield_pressure)
        self.model.mpm.yield_stress.fill_(yield_stress)

    def simulate(self):
        for i in range(self.sim_substeps):
            t = self.sim_time + (i + 1) * self.sim_dt
            self._update_melting_material(t)
            self._update_spoon(t)
            self.solver.step(self.state_0, self.state_1, None, None, self.sim_dt)
            self.solver.project_outside(self.state_1, self.state_1, self.sim_dt)
            self.state_0, self.state_1 = self.state_1, self.state_0

    @staticmethod
    def create_parser():
        parser = SpoonExample.create_parser()

        parser.add_argument("--melt-start", type=float, default=0.2, help="Time when melting begins [s]")
        parser.add_argument(
            "--melt-end",
            type=float,
            default=1.8,
            help="Time when melting reaches final material [s]; increase for more gradual softening",
        )

        parser.add_argument(
            "--melted-viscosity",
            type=float,
            default=20.0,
            help="Final plastic viscosity [Pa s]; raise to slow melted flow, lower for a runnier material",
        )
        parser.add_argument(
            "--melted-friction",
            type=float,
            default=0.02,
            help="Final friction coefficient; lower to reduce pressure-dependent shear strength",
        )
        parser.add_argument(
            "--melted-young-modulus",
            type=float,
            default=3.0e2,
            help="Final Young's modulus [Pa]; lower to make melted ice cream less elastically firm",
        )
        parser.add_argument(
            "--melted-damping",
            type=float,
            default=0.1,
            help="Final elastic damping relaxation time [s]; lower to reduce solid-like damping",
        )
        parser.add_argument(
            "--melted-yield-pressure",
            type=float,
            default=5.0e1,
            help="Final pressure yield limit [Pa]; lower first to make the scoop lose shape and flow",
        )
        parser.add_argument(
            "--melted-yield-stress",
            type=float,
            default=2.0e1,
            help="Final deviatoric yield stress [Pa]; lower first to make the scoop shear and slump",
        )

        return parser


if __name__ == "__main__":
    parser = Example.create_parser()

    viewer, args = newton.examples.init(parser)

    example = Example(viewer, args)

    newton.examples.run(example, args)
