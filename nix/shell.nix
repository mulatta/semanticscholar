{
  perSystem = {
    pkgs,
    config,
    ...
  }: {
    devShells.default = pkgs.mkShell {
      inputsFrom = [config.packages.default];
      packages = [
        pkgs.python3Packages.vcrpy
        pkgs.ruff
        pkgs.uv
      ];
    };
  };
}
