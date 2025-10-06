{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.poetry
    pkgs.nodejs-18_x
    pkgs.postgresql
    pkgs.openssl
    pkgs.libffi
    pkgs.playwright-driver.browsers
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
      pkgs.glib
      pkgs.xorg.libX11
    ];
    PLAYWRIGHT_BROWSERS_PATH = "${pkgs.playwright-driver.browsers}";
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = "1";
  };
}
