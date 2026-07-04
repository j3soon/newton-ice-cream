# Newton Ice Cream

Simulate ice cream in [Newton](https://github.com/newton-physics/newton) with MPM.

> As shown in the preview videos below, the current result is a material that kind of looks like ice cream, but it's not quite there yet. Planning to further tune the material parameters and document their effects in the near future (hopefully).

## Set up

Clone the repository:

```sh
git clone --recursive https://github.com/j3soon/newton-ice-cream.git
cd newton-ice-cream
```

Set up virtual environment and install dependencies:

```sh
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e "./newton[examples]"
```

For those who run within WSL, we may want to optimize the GPU performance with direct3d rendering by adding prefix `MESA_LOADER_DRIVER_OVERRIDE=d3d12 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA` in front of python scripts.

## Run Example

### Scooping Ice Cream

```sh
source .venv/bin/activate
python ./example_mpm_ice_cream_spoon.py
# For better fidelity, you can decrease the voxel size (with more computational cost):
python ./example_mpm_ice_cream_spoon.py --voxel-size 0.005
# If you have a powerful GPU but only have ~5 FPS, it may be due to OpenGL using llvmpipe software rendering. Try the following to force OpenGL to use your GPU:
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia python ./example_mpm_ice_cream_spoon.py
# If the command above freezes when using a remote desktop and needs to be killed with `kill <pid>`, try capping the render FPS.
python ./example_mpm_ice_cream_spoon.py --render-fps 15
# Melting ice cream
python ./example_mpm_melting_ice_cream_spoon.py
# For WSL users, the following command may give better performance with direct3d rendering:
MESA_LOADER_DRIVER_OVERRIDE=d3d12 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA python ./example_mpm_ice_cream_spoon.py
```

https://github.com/user-attachments/assets/297727db-86d2-40fd-a032-9e24c522e2d2

https://github.com/user-attachments/assets/6a320ab1-2690-4fcf-9ea5-e8d812993b21

written with minimal diff:

```sh
diff ./example_mpm_viscous.py ./example_mpm_ice_cream_spoon.py
code -d ./example_mpm_viscous.py ./example_mpm_ice_cream_spoon.py
```

### Flour on Spoon

```sh
source .venv/bin/activate
python ./example_mpm_granular_spoon.py
```

https://github.com/user-attachments/assets/00583488-207c-47bc-b333-9801122c7a34

written with minimal diff:

```sh
diff ./example_mpm_granular.py ./example_mpm_granular_spoon.py
code -d ./example_mpm_granular.py ./example_mpm_granular_spoon.py
```

## Assets

`assets/teaspoon` is created from Blender `Extra Mesh Objects` extension, with configs `Max Resolution: 15`, and applied `Recalculate Normals` afterwards. The object/mesh is also renamed to `Tea Spoon`. More details at: https://projects.blender.org/blender/blender/issues/158101

## Appendix

### Run Newton built-in examples

```sh
python -m newton.examples mpm_viscous
python -m newton.examples mpm_granular
```

### Choice of Simulation Engine

Newton MPM is a promising approach for simulating complex fluids and materials that are difficult to model with existing physics simulators. For example, Omniverse/Isaac Sim/Isaac Lab with the PhysX backend can simulate [soft bodies](https://nvidia-omniverse.github.io/PhysX/physx/5.4.1/docs/SoftBodies.html) and [particle-based fluids](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/particles/particles.html), but it remains challenging to simulate materials that fall in-between these two categories, such as ice cream. See related discussions here: https://github.com/isaac-sim/IsaacLab/issues/2953
