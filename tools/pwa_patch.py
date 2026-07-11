"""Applica il livello PWA a una cartella web già costruita da pygbag.

Copia web_extra/ (manifest, icone, service worker) nella cartella target e
inietta i tag necessari nell'<head> di index.html. NON tocca il gioco: il
service worker è un passacarte senza cache, quindi il comportamento resta
identico e ogni deploy è subito visibile.

Uso:  python tools/pwa_patch.py <cartella_web>     (es. build/web oppure _site)
"""
import os
import shutil
import sys

TAGS = """    <link rel="manifest" href="manifest.webmanifest">
    <meta name="theme-color" content="#0a0e1e">
    <link rel="icon" type="image/png" href="icons/favicon.png">
    <link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="AURIGA">
    <script>
      if ("serviceWorker" in navigator) {
        window.addEventListener("load", function () {
          navigator.serviceWorker.register("sw.js");
        });
      }
    </script>
"""


def main(target):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    extra = os.path.join(root, "web_extra")
    index = os.path.join(target, "index.html")
    if not os.path.isfile(index):
        raise SystemExit(f"index.html non trovato in {target}")

    # copia manifest, sw e icone
    shutil.copy(os.path.join(extra, "manifest.webmanifest"), target)
    shutil.copy(os.path.join(extra, "sw.js"), target)
    icons_dst = os.path.join(target, "icons")
    shutil.copytree(os.path.join(extra, "icons"), icons_dst, dirs_exist_ok=True)

    html = open(index, encoding="utf-8").read()
    if "manifest.webmanifest" in html:
        print("index.html già patchato: nessuna modifica")
        return
    if "</head>" not in html:
        raise SystemExit("index.html senza </head>: template pygbag cambiato?")
    html = html.replace("</head>", TAGS + "</head>", 1)
    open(index, "w", encoding="utf-8").write(html)
    print(f"PWA applicata a {target}: manifest, sw.js, {len(os.listdir(icons_dst))} icone, head patchato")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/web")
