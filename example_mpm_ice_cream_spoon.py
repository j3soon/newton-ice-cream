# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

"""Ice cream sphere scooped by a rotating teaspoon.

A cohesive viscoplastic ice cream sphere rests on the ground. A rigid
teaspoon sweeps through the sphere in four phases: orient, descend,
scoop, and lift, prescribed analytically via body_q / body_qd.
"""

import os

import numpy as np
import warp as wp
from pxr import Usd

import newton
import newton.examples
import newton.usd
from newton.solvers import SolverImplicitMPM


@wp.kernel
def _set_spoon_kinematic(
    body_index: int,
    x: float,
    y: float,
    z: float,
    r: float,
    vx: float,
    vz: float,
    r_dot: float,
    body_q: wp.array[wp.transform],
    body_qd: wp.array[wp.spatial_vector],
):
    q = wp.quat_from_axis_angle(wp.vec3(0.0, 1.0, 0.0), r)
    body_q[body_index] = wp.transform(wp.vec3(x, y, z), q)
    body_qd[body_index] = wp.spatial_vector(vx, 0.0, vz, 0.0, r_dot, 0.0)


class Example:
    def __init__(self, viewer, options):
        self.fps = options.fps
        self.frame_dt = 1.0 / self.fps

        self.sim_time = 0.0
        self.sim_substeps = options.substeps
        self.sim_dt = self.frame_dt / self.sim_substeps

        self.sphere_radius = options.sphere_radius

        self.viewer = viewer
        builder = newton.ModelBuilder()

        SolverImplicitMPM.register_custom_attributes(builder)

        # Teaspoon trajectory: list of (x, z, r) waypoints and the
        # duration of each segment between consecutive waypoints.
        self.waypoints = [
        #   (x         , z         , r         , t          ),
            (options.x0, options.z0, options.r0, 0.00),
            (options.x1, options.z1, options.r1, options.t1),
            (options.x2, options.z2, options.r2, options.t2),
            (options.x3, options.z3, options.r3, options.t3),
            (options.x4, options.z4, options.r4, options.t4),
        ]

        x0, z0, r0, _, _, _ = self._spoon_state_at(0.0)
        self.y_offset = float(options.y_offset)
        self.spoon_body = builder.add_body(
            xform=wp.transform(wp.vec3(x0, self.y_offset, z0), wp.quat_from_axis_angle(wp.vec3(0.0, 1.0, 0.0), r0)),
            label="spoon",
        )
        assets = os.path.join(os.path.dirname(__file__), "assets")
        usd_stage = Usd.Stage.Open(os.path.join(assets, "teaspoon", "teaspoon.usda"))
        spoon_mesh = newton.usd.get_mesh(usd_stage.GetPrimAtPath("/root/Tea_Spoon/Tea_Spoon"))
        s = options.spoon_scale
        builder.add_shape_mesh(
            body=self.spoon_body,
            xform=wp.transform(wp.vec3(0.0, 0.0, 0.0), wp.quat_identity()),
            mesh=spoon_mesh,
            scale=(s, s, s),
            cfg=newton.ModelBuilder.ShapeConfig(mu=options.spoon_friction, density=0.0),
        )

        # Create the ice cream particles
        Example.emit_particles(builder, options)

        builder.add_ground_plane(cfg=newton.ModelBuilder.ShapeConfig(mu=options.ground_friction))

        self.model = builder.finalize()
        self.model.set_gravity(options.gravity)

        # Set per-particle material properties
        # Reference: newton/_src/solvers/implicit_mpm/solver_implicit_mpm.py:714
        self.model.mpm.viscosity.fill_(options.viscosity)
        self.model.mpm.tensile_yield_ratio.fill_(options.tensile_yield_ratio)
        self.model.mpm.friction.fill_(options.friction)
        self.model.mpm.young_modulus.fill_(options.young_modulus)
        self.model.mpm.poisson_ratio.fill_(options.poisson_ratio)
        self.model.mpm.damping.fill_(options.damping)
        self.model.mpm.yield_pressure.fill_(options.yield_pressure)
        self.model.mpm.yield_stress.fill_(options.yield_stress)
        self.model.mpm.hardening.fill_(options.hardening)
        self.model.mpm.hardening_rate.fill_(options.hardening_rate)
        self.model.mpm.softening_rate.fill_(options.softening_rate)
        self.model.mpm.dilatancy.fill_(options.dilatancy)

        mpm_options = SolverImplicitMPM.Config()
        mpm_options.voxel_size = options.voxel_size
        mpm_options.tolerance = options.tolerance
        mpm_options.max_iterations = options.max_iterations
        mpm_options.strain_basis = options.strain_basis
        mpm_options.velocity_basis = options.velocity_basis
        mpm_options.collider_basis = options.collider_basis
        mpm_options.solver = options.solver

        self.solver = SolverImplicitMPM(self.model, mpm_options)

        self.state_0 = self.model.state()
        self.state_1 = self.model.state()

        self._update_spoon(0.0)

        self.viewer.show_particles = True
        self.viewer.set_model(self.model)
        if hasattr(self.viewer, "camera"):
            self.viewer.set_camera(pos=wp.vec3(-1.2, -0.8, 0.8), pitch=-30.0, yaw=30.0)

    # Returns (x, z, r, vx, vz, r_dot) for the spoon at time t by interpolating between waypoints.
    def _spoon_state_at(self, t):
        t_acc = 0.0
        for i in range(1, len(self.waypoints)):
            x1, z1, r1, dt = self.waypoints[i]
            if t < t_acc + dt:
                frac = (t - t_acc) / dt
                x0, z0, r0, _ = self.waypoints[i - 1]
                return (float(x0 + frac * (x1 - x0)), float(z0 + frac * (z1 - z0)), float(r0 + frac * (r1 - r0)),
                        float((x1 - x0) / dt), float((z1 - z0) / dt), float((r1 - r0) / dt))
            t_acc += dt
        x, z, r, _ = self.waypoints[-1]
        return float(x), float(z), float(r), 0.0, 0.0, 0.0

    def _update_spoon(self, t):
        x, z, r, vx, vz, r_dot = self._spoon_state_at(t)
        wp.launch(
            _set_spoon_kinematic,
            dim=1,
            inputs=[self.spoon_body, x, self.y_offset, z, r, vx, vz, r_dot,
                    self.state_0.body_q, self.state_0.body_qd],
            device=self.model.device,
        )

    def simulate(self):
        for i in range(self.sim_substeps):
            self._update_spoon(self.sim_time + (i + 1) * self.sim_dt)
            self.solver.step(self.state_0, self.state_1, None, None, self.sim_dt)
            self.state_0, self.state_1 = self.state_1, self.state_0

    def step(self):
        self.simulate()
        self.sim_time += self.frame_dt

    def test_final(self):
        pass

    def render(self):
        self.viewer.begin_frame(self.sim_time)
        self.viewer.log_state(self.state_0)
        self.viewer.end_frame()

    @staticmethod
    def emit_particles(builder, options):
        sphere_radius = options.sphere_radius
        spacing = options.voxel_size / 2.0
        dim = int(2.0 * sphere_radius / spacing) + 2
        axis = (np.arange(dim) - (dim - 1) * 0.5) * spacing
        pts = np.stack(np.meshgrid(axis, axis, axis, indexing="ij")).reshape(3, -1).T
        pts = pts[np.linalg.norm(pts, axis=1) <= sphere_radius]
        rng = np.random.default_rng(seed=42)
        pts += (rng.random(pts.shape) - 0.5) * spacing * 0.5
        pts += np.array([0.0, 0.0, sphere_radius])
        particle_mass = (spacing**3) * options.density
        print(f"Generating {len(pts)} ice cream particles...")
        builder.add_particles(
            pos=pts.tolist(),
            vel=np.zeros_like(pts).tolist(),
            mass=[particle_mass] * len(pts),
            radius=[spacing / 2.0] * len(pts),
        )

    @staticmethod
    def create_parser():
        parser = newton.examples.create_parser()

        parser.add_argument("--sphere-radius", type=float, default=0.10)
        parser.add_argument("--spoon-scale", type=float, default=0.50)
        parser.add_argument("--x0", type=float, default=-0.05)
        parser.add_argument("--z0", type=float, default=0.40)
        parser.add_argument("--r0", type=float, default=0.00)
        parser.add_argument("--x1", type=float, default=-0.05)
        parser.add_argument("--z1", type=float, default=0.40)
        parser.add_argument("--r1", type=float, default=float(-np.pi / 1.8))
        parser.add_argument("--x2", type=float, default=-0.05)
        parser.add_argument("--z2", type=float, default=0.07)
        parser.add_argument("--r2", type=float, default=float(-np.pi / 1.8))
        parser.add_argument("--x3", type=float, default=-0.20)
        parser.add_argument("--z3", type=float, default=0.05)
        parser.add_argument("--r3", type=float, default=0.00)
        parser.add_argument("--x4", type=float, default=-0.20)
        parser.add_argument("--z4", type=float, default=0.40)
        parser.add_argument("--r4", type=float, default=0.00)
        parser.add_argument("--y-offset", type=float, default=0.00)
        parser.add_argument("--t1", type=float, default=0.05)
        parser.add_argument("--t2", type=float, default=0.5)
        parser.add_argument("--t3", type=float, default=0.1)
        parser.add_argument("--t4", type=float, default=0.5)
        parser.add_argument("--gravity", type=float, nargs=3, default=[0, 0, -9.81])
        parser.add_argument("--fps", type=float, default=240.0)
        parser.add_argument("--substeps", type=int, default=1)
        # Material parameters
        parser.add_argument("--density", type=float, default=1000.0)
        parser.add_argument("--viscosity", type=float, default=1.0)
        parser.add_argument("--tensile-yield-ratio", "-tyr", type=float, default=1.0)
        parser.add_argument("--friction", "-mu", type=float, default=1.0)
        parser.add_argument("--ground-friction", type=float, default=2.0)
        parser.add_argument("--spoon-friction", type=float, default=2.0)
        parser.add_argument("--young-modulus", "-ym", type=float, default=1.0e4)
        parser.add_argument("--poisson-ratio", "-nu", type=float, default=0.35)
        parser.add_argument("--damping", type=float, default=0.9)
        parser.add_argument("--yield-pressure", "-yp", type=float, default=3.0e3)
        parser.add_argument("--yield-stress", "-ys", type=float, default=5.0e3)
        parser.add_argument("--hardening", type=float, default=0.0)
        parser.add_argument("--hardening-rate", type=float, default=1.0)
        parser.add_argument("--softening-rate", type=float, default=1.0)
        parser.add_argument("--dilatancy", type=float, default=0.0)

        # Solver parameters
        parser.add_argument(
            "--solver",
            "-s",
            type=str,
            default="auto",
        )
        parser.add_argument("--max-iterations", "-it", type=int, default=250)
        parser.add_argument("--tolerance", "-tol", type=float, default=1.0e-6)
        parser.add_argument("--voxel-size", "-dx", type=float, default=0.01)
        parser.add_argument("--strain-basis", "-sb", type=str, default="P0")
        parser.add_argument("--velocity-basis", "-vb", type=str, default="Q1")
        parser.add_argument("--collider-basis", "-cb", type=str, default="S2")

        return parser


if __name__ == "__main__":
    parser = Example.create_parser()

    viewer, args = newton.examples.init(parser)

    example = Example(viewer, args)

    newton.examples.run(example, args)
