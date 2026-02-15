{
  perSystem =
    { pkgs, ... }:
    let
      python = pkgs.python3;
    in
    {
      packages.default = python.pkgs.buildPythonApplication {
        pname = "semanticscholar-mcp";
        version = "0.11.0";
        format = "setuptools";
        src = ../.;

        propagatedBuildInputs = with python.pkgs; [
          httpx
          mcp
          nest-asyncio
          setuptools
          tenacity
        ];

        doCheck = false;
      };
    };
}
