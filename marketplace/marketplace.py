"""Marketplace (pendiente original): catálogo de Agent Images versionadas. Vista sobre datos, sin componente aparte."""

class Marketplace:
    def __init__(self):
        self._images: dict[str, list[dict]] = {}  # name -> [versiones]

    def publish(self, name: str, version: str, capabilities: list[str], author: str, description: str = ""):
        img = {"name": name, "version": version, "capabilities": capabilities,
               "author": author, "description": description}
        self._images.setdefault(name, []).append(img)
        return img

    def search(self, capability: str | None = None) -> list[dict]:
        out = []
        for versions in self._images.values():
            latest = versions[-1]
            if capability is None or capability in latest["capabilities"]:
                out.append(latest)
        return out

    def versions(self, name: str) -> list[dict]:
        return self._images.get(name, [])
