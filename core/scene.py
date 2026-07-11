"""Scene e SceneManager a stack.

Una scena con overlay=True lascia disegnare (ma non aggiornare) quella sotto:
utile per dialoghi e menu di pausa sopra l'esplorazione.
"""


class Scene:
    overlay = False

    def __init__(self, game):
        self.game = game

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    def on_resume(self, result=None):
        """Chiamata quando la scena sopra questa viene chiusa (pop)."""


class SceneManager:
    def __init__(self):
        self.stack = []

    @property
    def current(self):
        return self.stack[-1] if self.stack else None

    def push(self, scene):
        self.stack.append(scene)

    def pop(self, result=None):
        if self.stack:
            self.stack.pop()
        if self.current is not None:
            self.current.on_resume(result)

    def replace(self, scene):
        if self.stack:
            self.stack.pop()
        self.stack.append(scene)

    def clear_to(self, scene):
        self.stack = [scene]

    def draw(self, surface):
        """Disegna la scena corrente, includendo quelle sotto se overlay."""
        if not self.stack:
            return
        first = len(self.stack) - 1
        while first > 0 and self.stack[first].overlay:
            first -= 1
        for scene in self.stack[first:]:
            scene.draw(surface)
