{
  perSystem =
    { pkgs, ... }:
    let
      python = pkgs.python3;
      semanticscholar = python.pkgs.buildPythonApplication {
        pname = "semanticscholar";
        version = "0.11.0";
        pyproject = true;
        src = pkgs.lib.fileset.toSource {
          root = ../.;
          fileset = pkgs.lib.fileset.unions [
            ../pyproject.toml
            ../README.md
            ../semanticscholar
            ../tests
          ];
        };

        build-system = with python.pkgs; [ setuptools ];

        dependencies = with python.pkgs; [
          httpx
          nest-asyncio
          tenacity
        ];

        nativeCheckInputs = with python.pkgs; [
          pytestCheckHook
          vcrpy
        ];
      };
    in
    {
      packages = {
        inherit semanticscholar;
        default = semanticscholar;
      };

      checks = {
        inherit semanticscholar;
      };
    };
}
