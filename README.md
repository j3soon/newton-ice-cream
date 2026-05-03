# Newton Ice Cream

Simulate ice cream in [Newton](https://github.com/newton-physics/newton) with MPM.

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
uv pip install "./newton[examples]"
```

## Run built-in examples

```sh
python -m newton.examples
python -m newton.examples mpm_viscous
python -m newton.examples mpm_granular
```

## Assets

`assets/teaspoon` is created from Blender `Extra Mesh Objects` extension, with configs `Max Resolution: 15`, and applied `Recalculate Normals` afterwards. The object/mesh is also renamed to `Tea Spoon`. More details at: https://projects.blender.org/blender/blender/issues/158101
